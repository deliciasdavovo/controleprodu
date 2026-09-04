from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
old="""                                ) : linha.tipo === 'insumo' ? (
                                  <input value={x.name} onChange={(e) => onUpdateSupply({...x,name:e.target.value})} className=\"field h-8 px-2.5 text-[13px] font-semibold w-36 sm:w-48\" />
                                ) : (
                                  <input value={x.name} onChange={(e) => onUpdateProduct({...x,name:e.target.value})} className=\"field h-8 px-2.5 text-[13px] font-semibold w-36 sm:w-48\" />
                                )}"""
new="""                                ) : ehSupply ? (
                                  <input value={x.name} onChange={(e) => onUpdateSupply({...x,name:e.target.value})} className=\"field h-8 px-2.5 text-[13px] font-semibold w-36 sm:w-48\" />
                                ) : (
                                  <input value={x.name} onChange={(e) => onUpdateProduct({...x,name:e.target.value})} className=\"field h-8 px-2.5 text-[13px] font-semibold w-36 sm:w-48\" />
                                )}"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('internal catalog rows fixed')
