import fs from 'fs';
import path from 'path';
import { pathToFileURL } from 'url';
import puppeteer from 'puppeteer-core';

const requestPath=path.resolve(process.argv[2]);
const req=JSON.parse(fs.readFileSync(requestPath,'utf8'));
const html=req.source_paths.find(p=>/\.html?$/i.test(p));
if(!html) throw new Error('browser adapter needs an HTML source');
const chrome=process.env.CHROME;
if(!chrome) throw new Error('CHROME is not set');
fs.mkdirSync(req.output_dir,{recursive:true});
const browser=await puppeteer.launch({executablePath:chrome,headless:true,args:['--enable-webgl','--ignore-gpu-blocklist','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader','--enable-gpu']});
try{
  const page=await browser.newPage();
  const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  page.on('console',m=>{if(m.type()==='error') errors.push(m.text());});
  await page.setViewport({width:req.shot.width,height:req.shot.height,deviceScaleFactor:1});
  await page.goto(pathToFileURL(path.resolve(html)).href,{waitUntil:'load'});
  await new Promise(r=>setTimeout(r,150));
  const ready=await page.evaluate(()=>typeof window.renderFrameAt==='function');
  if(!ready) throw new Error('renderFrameAt unavailable: '+errors.join(' | '));
  for(const frame of req.frames){
    const t=req.shot.source_offset_seconds||0;
    const seconds=t+frame/req.shot.fps;
    await page.evaluate(({seconds,frame,shot})=>window.renderFrameAt(seconds,frame,shot),{seconds,frame,shot:req.shot});
    const target=path.join(req.output_dir,String(frame).padStart(6,'0')+'.png');
    await page.screenshot({path:target,type:'png',captureBeyondViewport:false});
    console.log('SHOT_FRAME '+frame);
  }
} finally { await browser.close(); }