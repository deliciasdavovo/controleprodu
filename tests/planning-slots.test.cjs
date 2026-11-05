const {test}=require('node:test');
const assert=require('node:assert/strict');
const {readFileSync}=require('node:fs');
const vm=require('node:vm');
const source=readFileSync(require('node:path').join(__dirname,'../src/app.jsx'),'utf8');
const layoutSource=source.slice(source.indexOf('      const planningSlotLayout ='),source.indexOf('      const PlanningSlotsBoard ='));
const layout=vm.runInNewContext(`${layoutSource}\nplanningSlotLayout`);
const positions=items=>Array.from(layout(items,'segunda'),p=>[p.id,p.position]);
test('legacy products retain their order in separate slots',()=>{
  assert.deepEqual(positions([{id:'b'},{id:'a'}]),[['b',1],['a',2]]);
});
test('multiple products share an explicit slot and preserve empty positions',()=>{
  assert.deepEqual(positions([{id:'a',positions:{segunda:4}},{id:'b',positions:{segunda:4}},{id:'c',positions:{segunda:7}}]),[['a',4],['b',4],['c',7]]);
});
test('new legacy products fill available spaces without displacing saved groups',()=>{
  assert.deepEqual(positions([{id:'a',positions:{segunda:1}},{id:'b',positions:{segunda:1}},{id:'c'}]),[['a',1],['b',1],['c',2]]);
});
test('slot assignments belong to their selected day',()=>{
  assert.deepEqual(positions([{id:'a',positions:{terca:5}},{id:'b'}]),[['a',1],['b',2]]);
});
const handlerSource=source.slice(source.indexOf('        const handlePositionPlanningProducts ='),source.indexOf('        // Registra a produção de fato',source.indexOf('        const handlePositionPlanningProducts =')));
function storage(fail=false){
  let rows=[{id:'a',unit:'vila',dayOfWeek:'segunda',productId:'a',displayOrder:1,idealQty:6}, {id:'b',unit:'vila',dayOfWeek:'segunda',productId:'b',displayOrder:2,idealQty:4}, {id:'c',unit:'matriz',dayOfWeek:'segunda',productId:'a',displayOrder:1,idealQty:10}, {id:'d',unit:'vila',dayOfWeek:'terca',productId:'a',displayOrder:1,idealQty:8}];
  const writes=[];
  const context={standardPlans:rows,currentUnit:'vila',setStandardPlans:fn=>rows=fn(rows),write:async(label,fn)=>{try{return await fn()}catch{return false}},run:async(table,query)=>{if(fail)throw Error('offline');writes.push(query)},sb:{from:()=>({update:values=>({eq:(key,id)=>({id,values})})})}};
  const move=vm.runInNewContext(`${handlerSource}\nhandlePositionPlanningProducts`,context);
  return {move,writes,rows:()=>rows};
}
test('moving a product into an occupied slot persists both products without changing quantities or other units/days',async()=>{
  const db=storage();assert.equal(await db.move('segunda',[{productId:'a',position:1},{productId:'b',position:1}]),true);
  assert.deepEqual(db.rows().map(p=>[p.id,p.displayOrder,p.idealQty]),[['a',-1,6],['b',-1,4],['c',1,10],['d',1,8]]);
  assert.deepEqual(db.writes.map(w=>w.id),['a','b']);
});
test('failed storage never updates the visible state as if the move succeeded',async()=>{
  const db=storage(true);assert.equal(await db.move('segunda',[{productId:'a',position:4}]),false);
  assert.equal(db.rows()[0].displayOrder,1);
});
test('invalid destination positions are rejected without writes',async()=>{
  const db=storage();for(const n of [0,-1,1.5,Infinity,10001])assert.equal(await db.move('segunda',[{productId:'a',position:n}]),false);
  assert.equal(db.writes.length,0);
});
