import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';
import {Presentation, PresentationFile, FileBlob} from '@oai/artifact-tool';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
process.env.RUNTIME_NODE_MODULES ??= path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const SKILL=process.env.PRESENTATIONS_SKILL_DIR || path.join(os.homedir(),'.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations');
const PY=process.env.RUNTIME_PYTHON || path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3');
const {resolvePresentationFont,applyPresentationChartFont,finalizePresentation}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')));
const BUILD=path.join(ROOT,'working','deck');
await fs.mkdir(BUILD,{recursive:true});
await fs.mkdir(path.join(ROOT,'preview','png'),{recursive:true});
const body=resolvePresentationFont({fontFamily:'Arial'});
const heading=resolvePresentationFont({fontFamily:'Georgia'});
const C={bg:'#FAF8F3',ink:'#163B36',teal:'#237E72',muted:'#58665F',orange:'#BD5A32',pale:'#EAF0EC',rule:'#CCD5CE',white:'#FFFFFF'};
const script=JSON.parse(await fs.readFile(path.join(ROOT,'code/script.json'),'utf8'));
const D=JSON.parse(await fs.readFile(path.join(ROOT,'code/slide_data.json'),'utf8'));
const assets={};
for(const n of ['residential-search-3d','property-decision-3d','lease-check-3d']) assets[n]=await fs.readFile(path.join(ROOT,'assets',n+'.png'));
const pres=Presentation.create({slideSize:{width:1280,height:720}});
const sources=[];

function text(s,t,x,y,w,h,size=28,color=C.ink,bold=false,font=body){
 const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 sh.text=t;sh.text.style={typeface:font,fontSize:size,color,bold,autoFit:'none',wrap:'square',insets:{left:0,right:0,top:0,bottom:0}};return sh;
}
function rect(s,x,y,w,h,fill){return s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:'none',width:0}});}
function slide(kicker,title,source){
 const s=pres.slides.add();s.background.fill=C.bg;const n=pres.slides.items.length;
 text(s,kicker.toUpperCase(),64,32,1110,25,16,C.orange,true);
 text(s,title,64,78,1150,98,42,C.ink,true,heading);
 text(s,source,64,672,1120,30,14,C.muted);text(s,String(n),1201,672,32,26,15,C.muted);
 sources.push(source);return s;
}
function fullArt(s,key){
 s.images.add({blob:assets[key],contentType:'image/png',alt:'Illustrative AI-generated 3D architecture; not an actual listing.',fit:'cover',position:{left:0,top:0,width:1280,height:720}});
 s.shapes.add({geometry:'rect',position:{left:0,top:0,width:840,height:720},fill:{type:'gradient',gradientKind:'linear',angleDeg:0,stops:[{offset:0,color:'#102E28'},{offset:61000,color:'#102E28/96'},{offset:100000,color:'#102E28/0'}]},line:{fill:'none',width:0}});
}
function table(s,rows,widths,x,y,h,font=25){
 const t=s.tables.add({rows:rows.length,columns:rows[0].length,left:x,top:y,width:widths.reduce((a,b)=>a+b,0),height:h,columnWidths:widths,values:rows});
 t.borders.assign({fill:C.rule,width:1,style:'solid'});
 for(let r=0;r<rows.length;r++)for(let c=0;c<rows[r].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?C.ink:(r%2?C.bg:C.pale);
  cell.text.style={typeface:body,fontSize:font,color:r===0?C.white:C.ink,bold:r===0,verticalAlignment:'middle',alignment:c===0?'left':'center',insets:{left:16,right:16,top:10,bottom:10}};
 } return t;
}
function columnChart(s,categories,values,colors,position,max=.5,direction='column'){
 // Excel embeds numeric chart data at 15 significant digits. Full precision
 // remains in the analysis JSON; the visible labels use one decimal percent.
 values=values.map(v=>Number(v.toPrecision(15)));
 const ch=s.charts.add('bar',{position,categories,series:[{name:'Share reaching the review threshold',values,valuesFormatCode:'0.0%',fill:C.teal,points:colors.map((fill,idx)=>({idx,fill}))}],barOptions:{direction,grouping:'clustered',gapWidth:110},hasLegend:false,
 xAxis:{visible:true,textStyle:{typeface:body,fontSize:23,fill:C.ink},majorGridlines:null,line:{fill:C.rule,width:1}},
 yAxis:{visible:true,min:0,max,majorUnit:.1,numberFormatCode:'0%',textStyle:{typeface:body,fontSize:19,fill:C.muted},majorGridlines:{fill:C.rule,width:.8}},
 dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:body,fontSize:31,fill:C.ink,bold:true}},chartFill:C.bg,chartLine:{fill:'none',width:0},plotAreaFill:C.bg,plotAreaLine:{fill:'none',width:0}});
 applyPresentationChartFont(ch,{fontFamily:body});return ch;
}
function intervalChart(s){
 const series=[];
 const precise=v=>Number(v.toPrecision(15));
 D.segments.forEach((v,i)=>{
  const color=i===2?C.orange:C.teal,y=3-i;
  series.push({name:v.label.replace('\n',' ')+': 90% range',xValues:[precise(v.lo),precise(v.hi)],values:[y,y],xValuesFormatCode:'0.0%',marker:{symbol:'none'},line:{fill:color,width:5}});
  series.push({name:v.label.replace('\n',' ')+': observed',xValues:[precise(v.share)],values:[y],xValuesFormatCode:'0.0%',fill:color,line:{fill:'none',width:0},marker:{symbol:'circle',size:13},dataLabelOverrides:[{idx:0,text:v.share_label,position:'top',showValue:false,textStyle:{typeface:body,fontSize:30,bold:true,fill:color}}]});
 });
 series.push({name:'All comparable listings: 25.3%',xValues:[...Array(2)].map(()=>precise(D.screening.values[0])),values:[.35,3.6],marker:{symbol:'none'},line:{fill:'#B9C0B8',width:2}});
 const ch=s.charts.add('scatter',{position:{left:451,top:213,width:765,height:357},series,scatterOptions:{style:'lineWithMarkers'},hasLegend:false,
  xAxis:{visible:true,min:0,max:.5,majorUnit:.1,numberFormatCode:'0%',textStyle:{typeface:body,fontSize:21,fill:C.muted},majorGridlines:null,line:{fill:C.rule,width:1}},
  yAxis:{visible:false,tickLabelPosition:'none',numberFormatCode:';;;',min:0,max:4,majorUnit:1,majorGridlines:null,line:{fill:'none',width:0}},
  dataLabels:{showValue:false,textStyle:{typeface:body,fontSize:29,fill:C.ink,bold:true}},chartFill:C.bg,chartLine:{fill:'none',width:0},plotAreaFill:C.bg,plotAreaLine:{fill:'none',width:0}});
 applyPresentationChartFont(ch,{fontFamily:body});return ch;
}
function selectedBreakdown(s){
 const ch=s.charts.add('bar',{position:{left:906,top:448,width:312,height:70},categories:['Selected'],series:[
  {name:'Reached 30 reviews',values:[423],fill:C.teal,line:{fill:'none',width:0}},
  {name:'Below 30 reviews',values:[546],fill:'#D9E0D9',line:{fill:'none',width:0}}
 ],barOptions:{direction:'bar',grouping:'stacked',gapWidth:0,overlap:100},hasLegend:false,
 xAxis:{visible:false,tickLabelPosition:'none',majorGridlines:null,line:{fill:'none',width:0}},yAxis:{visible:false,tickLabelPosition:'none',numberFormatCode:';;;',min:0,max:969,majorGridlines:null,line:{fill:'none',width:0}},
 dataLabels:{showValue:false,position:'center'},chartFill:C.bg,chartLine:{fill:'none',width:0},plotAreaFill:C.bg,plotAreaLine:{fill:'none',width:0}});
 applyPresentationChartFont(ch,{fontFamily:body});
}

// 1. The client decision, with original illustrative architecture.
{
 const s=pres.slides.add();fullArt(s,'residential-search-3d');sources.push('Inside Airbnb Melbourne, subject-supplied data; Group 2 analysis.');
 text(s,'THENEXTCHAPTER · GROUP 2',64,48,700,33,20,'#C6D9D1',true);
 text(s,'Where should\nwe look first?',64,147,650,180,63,C.white,true,heading);
 text(s,'Melbourne Airbnb\nA focused search before signing a lease',64,365,620,100,30,C.white);
 text(s,'Start with City of Melbourne\n2–3-bedroom apartments.',64,504,630,96,31,'#F1B98E',true);
 text(s,'Qihang Sun · Maksym Xu · Eric Huang · Loc Le',64,637,860,35,20,'#C6D9D1');
 text(s,'Illustrative 3D render',1046,680,205,24,14,'#C6D9D1');
}
// 2. Give the recommendation before the supporting detail.
{
 const s=slide('The client’s problem','Choosing a property before costs begin','Source: project brief. Review activity supports an initial search before individual property checks.');
 text(s,'The client plans to lease homes and offer short stays.',64,197,1120,55,32,C.ink,true);
 text(s,'Rent stays due when bookings fall.',64,269,1140,80,37,C.orange,true,heading);
 text(s,'THE BUSINESS QUESTION',64,386,490,35,20,C.teal,true);
 text(s,'Which homes deserve\nour limited search time?',64,444,580,115,38,C.ink,true);
 text(s,'THE ANALYTICAL QUESTION',752,386,465,35,20,C.teal,true);
 text(s,'Which property features relate\nto stronger past review activity?',752,444,460,123,31,C.ink);
 text(s,'A useful shortlist comes before permissions, quotes and a lease decision.',64,607,1150,51,27,C.teal);
}
// 3. Define the population and outcome without claiming 25% was forced.
{
 const s=slide('Data and measure','A fair comparison starts with similar homes','Source: subject-supplied Inside Airbnb data, collected 17 Jun–1 Jul 2026.');
 const xs=[64,466,877],nums=[D.sample.source_listings,D.sample.analysis_listings,D.sample.hosts],labels=['source listings','comparable listings','distinct hosts'];
 nums.forEach((n,i)=>{text(s,n.toLocaleString('en-AU'),xs[i],195,340,78,61,i?C.teal:C.muted,true);text(s,labels[i],xs[i],280,340,40,25,C.muted);});
 text(s,'Entire apartments and houses, 1–3 bedrooms, usable prices\nand at least one year since the first recorded review.',64,360,1140,91,30);
 text(s,'Our outcome: 30+ reviews in the previous 365 days.',64,483,1150,60,36,C.ink,true);
 text(s,'906 separate reference listings set the cutoff.\n25.3% of the analysis sample met it.',64,573,1150,72,27,C.teal);
}
// 4. Descriptive evidence for the search areas, including uncertainty.
{
 const s=slide('Finding 1 · where to search','City of Melbourne apartments lead the search','Source: observed segment shares; 90% uncertainty ranges from resampling hosts.');
 text(s,'Share reaching 30+ reviews: leading groups among 14 eligible groups',64,178,1140,47,28,C.muted);
 intervalChart(s);
 D.segments.forEach((v,i)=>{
  const y=272+i*79;
  text(s,v.label.replace('houses / townhouses','houses/townhouses')+` (n=${v.n.toLocaleString('en-AU')})`,64,y,385,69,22,C.ink,true);
 });
 text(s,'Dots show observed shares. Lines show 90% ranges.',451,570,764,34,21,C.muted);
 text(s,'Grey line: all 14 eligible groups combined, 25.3%.',451,604,764,34,21,C.muted);
 text(s,'Three promising options.\nCheck quotes and permissions.',64,573,365,78,25,C.teal,true);
}
// 5. An editable analytical flow with an explicit binary outcome.
{
 const s=slide('Our method','What the historical ranking score uses','Conditional associations, with other inputs held constant. Current settings may differ from the review year.');
 text(s,'Outcome (Y): 30+ reviews in the previous 365 days, yes or no.',64,172,1150,48,28,C.ink,true);
 text(s,'SIX INPUTS (X)',64,252,332,34,19,C.teal,true);
 text(s,'Council area\nDwelling type\nBedrooms\nPrice relative to peers\nAccepts one-night stays\nAmenity count',64,307,335,239,25);
 text(s,'LOGISTIC REGRESSION',453,252,340,34,19,C.teal,true);
 text(s,'Combines six features.\n\nOutput: a historical ranking score.',453,307,333,182,27);
 text(s,'Use the score to decide\nwhich homes to investigate.',453,505,335,93,25,C.muted);
 text(s,'TWO CONSISTENT ASSOCIATIONS',844,252,370,46,18,C.teal,true);
 text(s,'Accepts one-night stays',844,313,370,38,25,C.ink,true);
 text(s,'More likely to have\nreached 30 reviews',844,361,370,74,25,C.teal);
 text(s,'Price above similar homes',844,465,370,40,25,C.ink,true);
 text(s,'Less likely to have\nreached 30 reviews',844,514,370,74,25,C.orange);
 text(s,'Final main model: logistic regression for clarity. Interim random forest remains a benchmark.',64,621,1150,42,22,C.muted);
}
// 6. Like-for-like model comparison at the same expected search quota.
{
 const s=slide('Finding 2 · historical screening','The model found more high-review homes','Five host-grouped folds. Same expected screening quota: 969 homes. Ties share the remaining quota.');
 text(s,'Historical test across all 3,873 eligible homes',64,172,1150,45,29,C.muted);
 text(s,'Share of selected homes reaching 30+ reviews',64,235,810,43,25,C.ink);
 columnChart(s,['Simple group\naverages','Logistic\nmodel'],D.screening.values.slice(1),['#9FB3A8',C.teal],{left:45,top:288,width:815,height:288},.6,'bar');
 text(s,'423 / 969',919,265,300,63,47,C.teal,true,heading);
 text(s,'selected homes met\nthe review target.',919,345,300,79,26);
 selectedBreakdown(s);
 text(s,'546 did not meet it.',919,541,300,40,25,C.orange,true);
 text(s,'About 16 more target-reaching homes for every 100 selected.',64,596,1150,38,29,C.teal,true);
 text(s,'Test hosts were excluded from training. Future bookings and profit remain untested.',64,638,1150,29,21,C.muted);
}
// 7. A separate historical check of market groups, not the model.
{
 const s=slide('Finding 3 · a separate historical check','The same three groups stayed ahead','Source: one supplied snapshot of dated reviews; earlier reference sample sets 34. Same three groups as slide 4.');
 text(s,'Same 2,657 surviving homes. Two windows from one snapshot.',64,172,1150,44,30,C.ink,true);
 text(s,'A separate check uses 34 reviews as the target in both years.',64,224,1150,46,29,C.muted);
 text(s,'2024–25',64,321,404,45,33,C.teal,true);
 text(s,'Select the three\nleading property groups.',64,378,417,89,28);
 text(s,'2025–26',64,491,404,45,33,C.orange,true);
 text(s,'Check the same\nsurviving homes again.',64,547,424,90,28);
 text(s,'Reached 34+ reviews in the second year',520,307,691,42,25,C.ink);
 columnChart(s,['Other seven\ngroups','Earlier top\nthree groups'],[...D.temporal.values].reverse(),['#A6B8AD',C.orange],{left:515,top:360,width:711,height:222},.4,'bar');
 text(s,'Supports where to search.\nFuture model performance remains untested.',520,602,690,65,25,C.muted);
}
// 8. No synthetic weekly revenue ceilings: explicit lease decision gates.
{
 const s=slide('Before any lease','Two gates before any lease','Client decision framework. Check actual permissions and use explicit, conservative financial assumptions.');
 s.images.add({blob:assets['lease-check-3d'],contentType:'image/png',alt:'Illustrative 3D apartment model, brass key and blank lease documents.',fit:'contain',position:{left:835,top:167,width:390,height:461}});
 text(s,'01  PERMISSIONS',64,204,690,38,22,C.teal,true);
 text(s,'Confirm landlord consent and applicable\nbuilding and local requirements.',64,259,729,93,30,C.ink);
 text(s,'02  CONSERVATIVE CASH FLOW',64,385,738,38,22,C.teal,true);
 text(s,'Use real quotes and cautious income assumptions.\nCover rent, operating costs, setup allowance\nand a buffer agreed with the client.',64,440,732,123,28,C.ink);
 text(s,'Reject a candidate that fails either gate.',64,609,1040,48,32,C.orange,true);
 text(s,'Illustrative render',1060,637,160,22,13,C.muted);
}
// 9. A concrete proposal with people, timing and stop rules.
{
 const s=slide('Recommendations','A 30-day search with clear stop rules','Proposed workflow. Thirty days and ten candidates are planning choices, not model-derived optima.');
 const steps=[
  {x:64,week:'WEEK 1',owner:'Property scout',action:'Find 10 candidates.\nStart with city apartments.',decision:'Keep Yarra Ranges\nas a backup.'},
  {x:468,week:'WEEKS 2–3',owner:'Operator and analyst',action:'Verify permissions,\nquotes and cash flow.',decision:'Reject a home if\neither gate fails.'},
  {x:871,week:'WEEK 4',owner:'Business owner',action:'Compare the survivors.\nDecide on a small trial.',decision:'Proceed only if both\ngates pass.'}
 ];
 for(const p of steps){
  text(s,p.week,p.x,218,343,48,32,C.teal,true);
  text(s,p.owner,p.x,284,343,37,22,C.muted);
  text(s,p.action,p.x,372,343,109,28,C.ink,true);
  text(s,p.decision,p.x,519,343,88,26,C.orange);
 }
 text(s,'During a trial, track paid nights, cleaning workload and net cash flow.',64,630,1150,34,25,C.teal);
}
// 10. A precise approval request and a calm, memorable close.
{
 const s=pres.slides.add();fullArt(s,'property-decision-3d');sources.push('Group recommendations; decision remains subject to permission and verified cash-flow checks.');
 text(s,'THE DECISION TODAY',64,49,680,33,20,'#C6D9D1',true);
 text(s,'Approve a\nfocused search.',64,147,660,176,58,C.white,true,heading);
 text(s,'30 days. 10 candidates.\nCity of Melbourne apartments first.\nYarra Ranges houses as backup.',64,363,676,136,29,'#F1B98E',true);
 text(s,'Every lease still needs permission\nand a viable cash-flow case.',64,550,660,91,29,C.white);
 text(s,'Thank you. Questions?',64,668,740,36,22,'#C6D9D1');
 text(s,'Illustrative 3D render',1045,680,210,24,14,'#C6D9D1');
}

if(script.slides.length!==10)throw new Error('The speaking script must contain exactly 10 slides.');
for(let i=0;i<10;i++){
 const n=script.slides[i];
 const details=JSON.stringify(D.provenance[i]||{},null,2);
 const art=[0,7,9].includes(i)?'Illustrative 3D scene generated with OpenAI image_gen. This is not an actual listing. Assets and prompt provenance are included in assets/.':'';
 const ai=i===9?'AI acknowledgement: OpenAI Codex assisted with evidence organisation, drafting, code, slide and document layout, and checks. Image generation produced illustrative architectural scenes. Group members are responsible for checking and understanding the work.':'';
 pres.slides.items[i].speakerNotes.textFrame.setText(`${n.speaker} | ${n.seconds} seconds\n\n${n.script}\n\n中文排练提示: ${n.zh_cue}\n\nSource: ${sources[i]}\n${details}\n\nEvidence and code: https://github.com/maksym-xu/CMCE30005-TheNextChapter/tree/final-presentation-release-2026-10-01/final-presentation . See EVIDENCE_MAP.md for per-slide sources and the boundary between public aggregate checks and authorised-data reproduction. Raw school records and listing-level predictions are excluded from the public package.\n${art}\n${ai}`);
}
const raw=path.join(BUILD,'candidate-raw.pptx');
await (await PresentationFile.exportPptx(pres)).save(raw);
if(process.env.DRAFT_ONLY==='1'){
 for(let i=0;i<10;i++){
  const blob=await pres.export({slide:pres.slides.items[i],format:'png',scale:1.5});
  await fs.writeFile(path.join(ROOT,'preview/png',`slide-${i+1}.png`),new Uint8Array(await blob.arrayBuffer()));
 }
 console.log('Draft images only; no final presentation published.');
 process.exit(0);
}
const candidate=path.join(BUILD,'candidate-animated.pptx');
const styled=path.join(BUILD,'candidate-styled.pptx');
execFileSync(PY,[path.join(ROOT,'code/style_native_charts.py'),raw,styled],{stdio:'inherit'});
execFileSync(PY,[path.join(ROOT,'code/add_transitions.py'),styled,candidate],{stdio:'inherit'});
const finalPath=process.env.FINAL_PPTX || path.join(ROOT,'deliverables','TheNextChapter_Final.pptx');
const receipt=path.join(BUILD,path.basename(finalPath)+'.validation.json');
const result=await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath,pythonExecutable:PY,
 integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],
 explicitTotalSlideCount:10,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[4,6,7],materializeLiteralChartWorkbooks:true,
 fontPolicy:{basis:'design',families:[body,heading]},verifyArtifactToolImport:true,receiptPath:receipt});
console.log(JSON.stringify(result));
const finalPres=await PresentationFile.importPptx(await FileBlob.load(finalPath));
for(let i=0;i<10;i++){
 const blob=await finalPres.export({slide:finalPres.slides.items[i],format:'png',scale:1.5});
 await fs.writeFile(path.join(ROOT,'preview/png',`slide-${i+1}.png`),new Uint8Array(await blob.arrayBuffer()));
}
await fs.writeFile(path.join(BUILD,'built.json'),JSON.stringify({finalPath,slideCount:10,charts:[4,6,7],tables:[],fonts:[body,heading]},null,2));
console.log('Rendered all 10 final slides.');
