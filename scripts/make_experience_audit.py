#!/usr/bin/env python3
"""Make a local evidence-first audit page from a hash-bound findings document."""
import argparse, html, json, os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.core.media import sha256_file
from src.core.creative_qa import validate_report_evidence

def build(report_path, findings_path, output):
    report_path=Path(report_path).resolve();findings_path=Path(findings_path).resolve();output=Path(output).resolve()
    report=json.loads(report_path.read_text());findings=json.loads(findings_path.read_text())
    if findings["candidate_sha256"]!=report["media_sha256"]:
        raise ValueError("findings do not match candidate")
    checked=validate_report_evidence(report_path)
    if not checked["pass"]:raise ValueError("audit evidence invalid: "+str(checked["errors"]))
    if sha256_file(report["media"])!=report["media_sha256"]:raise ValueError("candidate changed")
    output.parent.mkdir(parents=True,exist_ok=True)
    h=html.escape
    def url(path):return h(os.path.relpath(path,output.parent))
    cards=[]
    points={p["id"]:p for p in report["evidence"]["review_points"]}
    for item in findings["findings"]:
        p=points.get(item.get("point_id"))
        media=""
        if p:
            media=f'<img loading="lazy" src="{url(report_path.parent/p["phone_frame"])}" alt="Exact candidate frame"><video controls preload="none" src="{url(report_path.parent/p["normal_speed_clip"])}"></video>'
        cards.append(f'<article><div class="tag">{h(item["basis"])} · {h(item["priority"])}</div><h2>{h(item["title"])}</h2><p>{h(item["observed"])}</p><p><b>Repair:</b> {h(item["repair"])}</p>{media}</article>')
    signals=report["signals"].get("authored_audio_intent",{})
    tables=[]
    for e in signals.get("events",[]):
        m=e["master"]
        tables.append(f'<tr><td>{h(str(e["event_id"]))}</td><td>{e["at_seconds"]:.2f}s</td><td>{m.get("rms_dbfs","—")}</td><td>{m.get("loudest_50ms_rms_dbfs","—")}</td><td>{h(e["scope"])}</td></tr>')
    page='<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    page+='<title>SECOND EARTH · independent workflow audit</title><style>body{background:#10151c;color:#e9eef3;font:17px/1.65 system-ui;margin:0}main{max-width:960px;margin:auto;padding:24px}h1{line-height:1.2}h2{font-size:22px}a{color:#7cd4e9}article{background:#19232d;padding:22px;margin:18px 0;border-radius:12px}.tag{color:#e5c273;font-size:14px}img{width:360px;max-width:100%;vertical-align:top}video{width:100%;max-height:420px;margin-top:15px}code{overflow-wrap:anywhere;font-size:12px}td,th{padding:8px;border-bottom:1px solid #43505d;text-align:left}table{width:100%;font-size:13px}.note{border-left:3px solid #e5c273;padding:12px}</style><main>'
    page+='<h1>SECOND EARTH<br>Independent workflow audit</h1>'
    page+=f'<p class="note">{h(findings["verdict"])}</p><p>Exact candidate: <code>{h(report["media_sha256"])}</code></p>'
    page+=f'<p>{h(findings["capability_proof"])}</p><p><b>Review limit:</b> {h(findings["review_limit"])}</p>'
    page+=f'<video controls preload="metadata" src="{url(Path(report["media"]))}"></video>'
    page+=f'<p>{report["review_coverage"]["generated_point_count"]} review points generated. Evidence generation is separate from completed inspection.</p>'
    page+=''.join(cards)
    page+='<h2>Authored silence versus delivered audio</h2><p>Measured from the encoded master. These are measurements, not listening judgments. Missing scope requires resolution before approval.</p><table><tr><th>Event</th><th>Time</th><th>RMS dBFS</th><th>Loudest 50 ms</th><th>Scope</th></tr>'+''.join(tables)+'</table>'
    page+=f'<p><a href="{url(report_path)}">Full machine-readable audit</a> · <a href="{url(findings_path)}">Findings and repair priorities</a></p></main>'
    output.write_text(page)
    return {"output":str(output),"candidate_sha256":report["media_sha256"],"evidence_count":checked["evidence_count"]}

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("report");p.add_argument("findings");p.add_argument("output")
    a=p.parse_args();print(json.dumps(build(a.report,a.findings,a.output),indent=2))
