from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import os,re

class PlayerHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        self._remaining=None
        value=self.headers.get("Range")
        path=self.translate_path(self.path)
        if not value or not os.path.isfile(path):
            return super().send_head()
        m=re.fullmatch(r"bytes=(\d*)-(\d*)",value.strip())
        if not m:
            return super().send_head()
        size=os.path.getsize(path)
        if m[1]:
            start=int(m[1]); end=min(int(m[2]) if m[2] else size-1,size-1)
        else:
            start=max(0,size-int(m[2] or "0")); end=size-1
        if start>=size or start>end:
            self.send_response(416); self.send_header("Content-Range",f"bytes */{size}"); self.end_headers(); return None
        f=open(path,"rb"); f.seek(start)
        self.send_response(206)
        self.send_header("Content-type",self.guess_type(path))
        self.send_header("Content-Length",str(end-start+1))
        self.send_header("Content-Range",f"bytes {start}-{end}/{size}")
        self.send_header("Accept-Ranges","bytes")
        self.end_headers()
        self._remaining=end-start+1
        return f
    def copyfile(self,src,dst):
        if self._remaining is None:
            return super().copyfile(src,dst)
        remaining=self._remaining
        try:
            while remaining:
                chunk=src.read(min(1024*1024,remaining))
                if not chunk: break
                dst.write(chunk); remaining-=len(chunk)
        except (BrokenPipeError,ConnectionResetError):
            pass
    def end_headers(self):
        self.send_header("Cache-Control","no-cache")
        super().end_headers()

ThreadingHTTPServer(("127.0.0.1",8880),PlayerHandler).serve_forever()
