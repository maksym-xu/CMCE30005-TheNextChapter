#!/usr/bin/env python3
"""Build an offline image-based HTML preview and 16:9 PDF from ten PNG slides.

Usage: bundled-python build_preview.py ROOT
Reads ROOT/preview/png/slide-N.png (N=1..10). Writes Animated_Preview.html and
Slide_Preview.pdf under ROOT/preview. The HTML is a rendering preview, not a
PowerPoint playback test; optional four-second autoplay starts paused.
"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import re

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


TEMPLATE = r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>TheNextChapter · Animated Slide Preview</title>
<style>
:root{color-scheme:dark;font-family:Arial,"PingFang SC","Microsoft YaHei",sans-serif;background:#101b1b;color:#eff6f2}
*{box-sizing:border-box}body{margin:0;min-height:100vh;min-height:100dvh;display:flex;flex-direction:column}
header{padding:15px 24px 8px;max-width:1440px;width:100%;margin:auto}
h1{font-size:18px;margin:0 0 6px;font-weight:600}p{font-size:13px;line-height:1.5;margin:0;color:#c2d2cb}
main{flex:1;display:grid;place-items:center;min-height:0;padding:12px 24px}
#stage{position:relative;width:min(100%,calc((100dvh - 180px)*16/9));aspect-ratio:16/9;overflow:hidden;background:#000;box-shadow:0 12px 45px #0006;border-radius:5px}
.slide{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;opacity:0;transition:opacity 600ms ease}
.slide.visible{opacity:1}.slide.under{opacity:1;transition:none}
footer{padding:4px 24px 15px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;justify-content:center}
button{font:inherit;font-size:14px;color:#eff6f2;background:#27483e;border:1px solid #617c70;border-radius:7px;padding:10px 14px;cursor:pointer}
button:hover{background:#355f52}button:focus-visible{outline:3px solid #e6bd80;outline-offset:3px}button:disabled{opacity:.4;cursor:default}
#counter{min-width:92px;text-align:center;font-variant-numeric:tabular-nums;font-size:14px}
#status{font-size:12px;color:#c2d2cb;flex-basis:100%;text-align:center}
#stage:fullscreen{width:100vw;height:100vh;border-radius:0;aspect-ratio:auto;background:#000;box-shadow:none}
@media(max-width:640px){header{padding:10px 12px 4px}main{padding:8px 10px}footer{padding:5px 10px 10px;gap:6px}button{padding:8px 10px;font-size:12px}#stage{width:100%}h1{font-size:16px}}
@media(prefers-reduced-motion:reduce){.slide{transition:none}}
</style>
</head>
<body>
<header>
<h1>TheNextChapter · 动态幻灯片预览</h1>
<p>这是最终幻灯片渲染图的淡入预览，不是 PowerPoint 动画播放验证。左右箭头或空格翻页；F 全屏。四秒轮播仅用于预览，默认暂停。</p>
</header>
<main><div id="stage" role="region" aria-label="幻灯片预览" tabindex="0">
<img id="back" class="slide" alt="" aria-hidden="true">
<img id="front" class="slide visible" alt="第 1 页">
</div></main>
<footer>
<button id="prev" type="button" aria-label="上一页">← 上一页</button>
<span id="counter" aria-live="polite" aria-atomic="true"></span>
<button id="next" type="button" aria-label="下一页">下一页 →</button>
<button id="play" type="button" aria-pressed="false">播放预览（4秒/页）</button>
<button id="full" type="button">全屏</button>
<div id="status" role="status">已暂停 · 4 秒/页仅为预览速度，不代表正式演讲时间。</div>
</footer>
<script>
'use strict';
const slides=__SLIDES_DATA__;
let current=0, autoplay=null, animationId=0;
const stage=document.getElementById('stage'),front=document.getElementById('front'),back=document.getElementById('back');
const prev=document.getElementById('prev'),next=document.getElementById('next'),counter=document.getElementById('counter');
const play=document.getElementById('play'),full=document.getElementById('full'),status=document.getElementById('status');
function refresh(){counter.textContent=`${current+1} / ${slides.length}`;prev.disabled=current===0;next.disabled=current===slides.length-1;}
async function show(index){
  index=Math.max(0,Math.min(slides.length-1,index));if(index===current)return;
  const token=++animationId,old=front.src;current=index;refresh();
  const incoming=new Image();incoming.src=slides[index].src;
  try{await incoming.decode();}catch(e){}
  if(token!==animationId)return;
  back.src=old;back.className='slide under';
  front.style.transition='none';front.className='slide';front.src=incoming.src;front.alt=`第 ${index+1} 页`;
  void front.offsetWidth;front.style.transition='';
  requestAnimationFrame(()=>{if(token===animationId)front.className='slide visible';});
}
function pause(){if(autoplay!==null)clearInterval(autoplay);autoplay=null;play.textContent='播放预览（4秒/页）';play.setAttribute('aria-pressed','false');status.textContent='已暂停 · 4 秒/页仅为预览速度，不代表正式演讲时间。';}
function togglePlay(){if(autoplay!==null){pause();return;}autoplay=setInterval(()=>show((current+1)%slides.length),4000);play.textContent='暂停预览';play.setAttribute('aria-pressed','true');status.textContent='正在轮播 · 4 秒/页仅为预览速度，不代表正式演讲时间。';}
async function toggleFull(){try{if(document.fullscreenElement)await document.exitFullscreen();else await stage.requestFullscreen();}catch(e){status.textContent='此浏览器不支持网页全屏；可使用浏览器自身的全屏菜单。';}}
prev.addEventListener('click',()=>{pause();show(current-1);});next.addEventListener('click',()=>{pause();show(current+1);});
play.addEventListener('click',togglePlay);full.addEventListener('click',toggleFull);
document.addEventListener('fullscreenchange',()=>{full.textContent=document.fullscreenElement?'退出全屏':'全屏';});
document.addEventListener('keydown',e=>{
  if(e.altKey||e.ctrlKey||e.metaKey||['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName))return;
  if(e.key===' '&&e.target.tagName==='BUTTON')return;
  if(['ArrowRight','ArrowDown','PageDown',' '].includes(e.key)){e.preventDefault();pause();show(current+1);}
  else if(['ArrowLeft','ArrowUp','PageUp'].includes(e.key)){e.preventDefault();pause();show(current-1);}
  else if(e.key==='Home'){e.preventDefault();pause();show(0);}
  else if(e.key==='End'){e.preventDefault();pause();show(slides.length-1);}
  else if(e.key.toLowerCase()==='f'){e.preventDefault();toggleFull();}
});
document.addEventListener('visibilitychange',()=>{if(document.hidden)pause();});
front.src=slides[0].src;refresh();
</script>
</body></html>
'''


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    preview = root / "preview"
    png_dir = preview / "png"
    pattern = re.compile(r"slide-(\d+)\.png\Z")
    images = sorted((p for p in png_dir.glob("slide-*.png") if pattern.fullmatch(p.name)),
                    key=lambda p: int(pattern.fullmatch(p.name).group(1)))
    if [int(pattern.fullmatch(p.name).group(1)) for p in images] != list(range(1, 11)):
        raise ValueError("Expected exactly slide-1.png through slide-10.png")
    for p in images:
        with Image.open(p) as im:
            im.verify()
        with Image.open(p) as im:
            if abs(im.width / im.height - 16 / 9) > 0.02:
                raise ValueError(f"Expected a 16:9 slide image: {p.name} ({im.width} x {im.height})")

    payload = [{"name": p.name, "src": "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")}
               for p in images]
    html = preview / "Animated_Preview.html"
    html.write_text(TEMPLATE.replace("__SLIDES_DATA__", json.dumps(payload, separators=(",", ":"))), encoding="utf-8")

    pdf = preview / "Slide_Preview.pdf"
    page_w, page_h = 960, 540
    doc = canvas.Canvas(str(pdf), pagesize=(page_w, page_h), pageCompression=1)
    doc.setTitle("TheNextChapter Final Presentation — Rendered Slide Preview")
    doc.setAuthor("TheNextChapter — Group 2")
    doc.setSubject("Ten rendered slide images; this PDF is not an animation playback test.")
    for p in images:
        with Image.open(p) as source:
            rgba = source.convert("RGBA")
            flattened = Image.new("RGBA", rgba.size, "white")
            flattened.alpha_composite(rgba)
            rgb = flattened.convert("RGB")
            scale = min(page_w / rgb.width, page_h / rgb.height)
            w, h = rgb.width * scale, rgb.height * scale
            doc.setFillColorRGB(1, 1, 1)
            doc.rect(0, 0, page_w, page_h, fill=1, stroke=0)
            doc.drawImage(ImageReader(rgb), (page_w-w)/2, (page_h-h)/2, width=w, height=h)
            doc.showPage()
    doc.save()
    print(json.dumps({"html": str(html), "pdf": str(pdf), "slides": len(images),
                      "offline_embedded_images": True, "default_autoplay": False,
                      "optional_preview_interval_seconds": 4, "pdf_aspect_ratio": "16:9",
                      "powerpoint_playback_verified": False}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
