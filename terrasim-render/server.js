import express from 'express';
const app = express();
app.use(express.json({limit:'256kb'}));
app.use(express.static('public'));
app.get('/api/health', (_req,res) => res.set('Cache-Control','no-store').json({ok:true,provider:process.env.AI_API_KEY?'AI provider configured':'Render backend ready; AI key missing',model:process.env.AI_MODEL||'gpt-4.1-mini',aiReady:Boolean(process.env.AI_API_KEY)}));
const goals=['Grow food','Gather wood','Gather stone','Research','Trade goods','Improve road','Build home','Build farm','Build workshop','Build well','Build school','Build clinic','Build hall','Rest','Eat'];
app.post('/api/plan', async (req,res) => {
 res.set('Cache-Control','no-store');
 const apiKey=process.env.AI_API_KEY||'';
 if(!apiKey) return res.status(503).json({error:'Set AI_API_KEY in Render Environment settings, then redeploy.'});
 const agents=req.body?.agents;
 if(!Array.isArray(agents)||agents.length<1||agents.length>50) return res.status(400).json({error:'Expected 1–50 agents.'});
 const base=(process.env.AI_BASE_URL||'https://api.openai.com/v1').replace(/\/$/,'');
 const model=process.env.AI_MODEL||'gpt-4.1-mini';
 try {
  const prompt='Plan one in-game goal per agent for a fictional civilization. Consider hunger, energy, resources, skills, roles, buildings and memories. Return only JSON: {"plans":[{"id":1,"goal":"Grow food","reason":"short reason"}]}. Allowed goals: '+goals.join(', ')+'. No real-world actions, payments or network tasks. World state: '+JSON.stringify(req.body);
  const upstream=await fetch(base+'/chat/completions',{method:'POST',headers:{authorization:'Bearer '+apiKey,'content-type':'application/json'},body:JSON.stringify({model,temperature:0.2,response_format:{type:'json_object'},messages:[{role:'system',content:'You are a planning engine for a fictional city simulation. Return valid JSON only.'},{role:'user',content:prompt}]})});
  const raw=await upstream.text();let data;try{data=JSON.parse(raw)}catch{data={error:raw.slice(0,250)}}
  if(!upstream.ok)return res.status(502).json({error:data.error?.message||data.error||'AI provider HTTP '+upstream.status});
  let parsed;try{parsed=JSON.parse(data.choices?.[0]?.message?.content||'{}')}catch{return res.status(502).json({error:'AI response was not valid JSON'})}
  const ids=new Set(agents.map(a=>Number(a.id))),seen=new Set();
  const plans=(Array.isArray(parsed.plans)?parsed.plans:[]).filter(p=>ids.has(Number(p.id))&&!seen.has(Number(p.id))&&goals.includes(p.goal)&&(seen.add(Number(p.id)),true)).map(p=>({id:Number(p.id),goal:p.goal,reason:String(p.reason||'AI-selected goal').slice(0,120)}));
  return res.json({ok:true,model,plans});
 } catch(e){return res.status(400).json({error:'Planning request failed: '+String(e.message||e).slice(0,160)})}
});
const port=process.env.PORT||3000;app.listen(port,'0.0.0.0',()=>console.log('TerraSim backend listening on '+port));
