import fs from 'fs';
import path from 'path';
import {spawn} from 'child_process';
import {pathToFileURL} from 'url';
import puppeteer from '../../../../src/renderers/canvas_handdrawn/node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js';

const here=path.dirname(new URL(import.meta.url).pathname);
const prod=path.resolve(here,'..');
const plan=JSON.parse(fs.readFileSync(path.join(prod,'source/execution-plan.json'),'utf8'));
const shotIds=new Set(['shot-03','shot-05','shot-06','shot-09','shot-13','shot-18']);
const chrome=process.env.CHROME||'/data/data/com.termux/files/usr/bin/chromium-browser';
const outDir=path.join(prod,'renders');fs.mkdirSync(outDir,{recursive:true});
const browser=await puppeteer.launch({executablePath:chrome,headless:true});
const page=await browser.newPage();await page.setViewport({width:1280,height:720,deviceScaleFactor:1});
await page.goto(pathToFileURL(path.join(here,'canvas_world.html')).href,{waitUntil:'load'});
for(const shot of plan.shots.filter(s=>shotIds.has(s.id))){
  const out=path.join(outDir,shot.id+'.mp4');
  if(fs.existsSync(out)){console.log('SKIP',shot.id);continue}
  const ff=spawn('ffmpeg',['-y','-v','error','-f','image2pipe','-framerate','24','-vcodec','png','-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',out],{stdio:['pipe','inherit','inherit']});
  const frames=Math.round(shot.duration_seconds*24);
  for(let i=0;i<frames;i++){
    const t=i/24;
    await page.evaluate(({id,t,d})=>window.renderShotAt(id,t,d),{id:shot.id,t,d:shot.duration_seconds});
    const png=await page.screenshot({type:'png',captureBeyondViewport:false});
    if(!ff.stdin.write(png)) await new Promise(r=>ff.stdin.once('drain',r));
  }
  ff.stdin.end();const code=await new Promise(r=>ff.on('close',r));
  if(code!==0)throw new Error('ffmpeg failed '+shot.id);
  console.log('CANVAS_DONE',shot.id,frames);
}
await browser.close();
