from PIL import Image,ImageDraw
def render_frame(shot,frame_index,output_path,request):
    w,h=int(shot["width"]),int(shot["height"])
    t=frame_index/float(shot["fps"])
    im=Image.new("RGB",(w,h),(16,22,36))
    d=ImageDraw.Draw(im)
    x=int((.15+.7*((t%1.0))) * w)
    d.ellipse((x-24,h//2-24,x+24,h//2+24),fill=(230,180,70))
    d.text((18,18),f"PYTHON {frame_index}",fill="white")
    im.save(output_path)
