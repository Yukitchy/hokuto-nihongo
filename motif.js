/* Motif preview switcher: append ?motif=a|b|c (or ?motif=0 for current). Absent = default design, no UI. */
(function(){
  var q=new URLSearchParams(location.search); if(!q.has('motif'))return;
  var m=q.get('motif'); if(/^[abc]$/.test(m))document.documentElement.dataset.motif=m; else delete document.documentElement.dataset.motif;
  document.addEventListener('DOMContentLoaded',function(){
    var opts=[['b','B ライナーノーツ(採用)'],['a','A ジン'],['c','C 朱インク'],['0','旧・マンガ原稿']];
    var bar=document.createElement('div');bar.className='motif-picker';
    opts.forEach(function(o){var b=document.createElement('button');b.textContent=o[1];b.className=(o[0]===m||(o[0]==='0'&&!/^[abc]$/.test(m)))?'on':'';
      b.onclick=function(){q.set('motif',o[0]);location.search=q.toString();};bar.appendChild(b);});
    document.body.appendChild(bar);
  });
})();
