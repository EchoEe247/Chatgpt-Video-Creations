#!/usr/bin/env python3
"""Serve a local directory with HTTP byte-range support for seekable media."""
from __future__ import annotations

import argparse
import os
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class RangeHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control","no-store")
        self.send_header("Accept-Ranges","bytes")
        super().end_headers()

    def send_head(self):
        path=self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()
        try:
            f=open(path,"rb")
        except OSError:
            self.send_error(404,"File not found")
            return None
        fs=os.fstat(f.fileno()); size=fs.st_size
        rng=self.headers.get("Range")
        if rng:
            m=re.fullmatch(r"bytes=(\d*)-(\d*)",rng.strip())
            if m:
                if m.group(1):
                    start=int(m.group(1)); end=int(m.group(2) or size-1)
                elif m.group(2):
                    tail=min(int(m.group(2)),size); start=size-tail; end=size-1
                else:
                    start=0; end=size-1
                end=min(end,size-1)
                if 0<=start<=end<size:
                    self.send_response(206)
                    self.send_header("Content-type",self.guess_type(path))
                    self.send_header("Content-Range",f"bytes {start}-{end}/{size}")
                    self.send_header("Content-Length",str(end-start+1))
                    self.send_header("Last-Modified",self.date_time_string(fs.st_mtime))
                    self.end_headers()
                    self._range=(start,end); f.seek(start); return f
            f.close()
            self.send_error(416,"Requested Range Not Satisfiable")
            return None
        self._range=None
        self.send_response(200)
        self.send_header("Content-type",self.guess_type(path))
        self.send_header("Content-Length",str(size))
        self.send_header("Last-Modified",self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def copyfile(self,source,outputfile):
        if getattr(self,"_range",None):
            start,end=self._range; remaining=end-start+1
            while remaining:
                chunk=source.read(min(64*1024,remaining))
                if not chunk: break
                outputfile.write(chunk); remaining-=len(chunk)
        else:
            super().copyfile(source,outputfile)


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",required=True)
    ap.add_argument("--host",default="127.0.0.1")
    ap.add_argument("--port",type=int,default=8878)
    args=ap.parse_args()
    root=Path(args.root).resolve()
    if not root.is_dir(): raise SystemExit(f"missing root: {root}")
    os.chdir(root)
    server=ThreadingHTTPServer((args.host,args.port),RangeHandler)
    print(f"http://{args.host}:{args.port}/",flush=True)
    server.serve_forever()


if __name__=="__main__":
    main()
