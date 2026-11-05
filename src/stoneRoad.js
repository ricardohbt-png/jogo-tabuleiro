(function(root){
  'use strict';
  function strokeCells(anchor, end, axis, width, gridWidth, gridHeight){
    const dx=end[0]-anchor[0], dy=end[1]-anchor[1], out=[];
    const first=-Math.floor((width-1)/2);
    for(let i=0;i<=Math.abs(dx||dy);i++) for(let j=0;j<width;j++){
      const x=anchor[0]+Math.sign(dx)*i+(axis==='y'?first+j:0);
      const y=anchor[1]+Math.sign(dy)*i+(axis==='x'?first+j:0);
      if(x>=0&&y>=0&&x<gridWidth&&y<gridHeight) out.push([x,y]);
    }
    return out;
  }
  function neighborMask(occupied,x,y){
    return (occupied.has(`${x},${y-1}`)?1:0)|(occupied.has(`${x+1},${y}`)?2:0)
      |(occupied.has(`${x},${y+1}`)?4:0)|(occupied.has(`${x-1},${y}`)?8:0);
  }
  const cache=new Map();
  function wideTile(image,mask){
    if(cache.has(mask)) return cache.get(mask);
    if(!image || !image.naturalWidth) return null;
    const cv=document.createElement('canvas'); cv.width=cv.height=256;
    const c=cv.getContext('2d');
    const w=image.naturalWidth, h=image.naturalHeight;
    for(let y=0;y<2;y++) for(let x=0;x<2;x++){
      c.save(); c.translate(x*128+(x?128:0),y*128+(y?128:0)); c.scale(x?-1:1,y?-1:1);
      c.drawImage(image,w*.34,h*.34,w*.32,h*.32,0,0,128,128); c.restore();
    }
    c.globalCompositeOperation='destination-in';
    for(const [bit,x0,y0,x1,y1] of [[1,0,0,0,50],[2,256,0,206,0],[4,0,256,0,206],[8,0,0,50,0]]){
      if(mask&bit) continue;
      const g=c.createLinearGradient(x0,y0,x1,y1); g.addColorStop(0,'rgba(0,0,0,0)'); g.addColorStop(1,'rgba(0,0,0,1)');
      c.fillStyle=g; c.fillRect(0,0,256,256);
    }
    c.globalCompositeOperation='source-over'; cache.set(mask,cv); return cv;
  }
  const api={strokeCells,neighborMask,wideTile};
  if(typeof module!=='undefined' && module.exports) module.exports=api;
  else root.StoneRoad=api;
})(typeof window!=='undefined'?window:globalThis);
