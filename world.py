import heapq
import random
from collections import deque

from data import VARIANTES_TERRENO, RENDIMENTOS_TERRENO, MELHORIAS, CONFIG_RIOS

PASSAVEIS_TERRA = {'Grama', 'Deserto', 'Neve'}
PASSAVEIS_MAR = {'Água Rasa', 'Água Profunda'}
PASSAVEIS_MAR_RASO = {'Água Rasa'}

VIZINHOS_8 = (
    (-1, -1), (0, -1), (1, -1),
    (-1,  0),          (1,  0),
    (-1,  1), (0,  1), (1,  1),
)
VIZINHOS_4 = ((0,-1), (1,0), (0,1), (-1,0))


def normalizar_aresta(a, b):
    return tuple(sorted((tuple(a), tuple(b))))


class Mundo:
    def __init__(self, largura, altura, percentuais, seed=None):
        self.largura = largura
        self.altura = altura
        self.percentuais = percentuais
        self.random = random.Random(seed)
        self.tiles = self.gerar_mapa()
        self._classificar_aguas()
        self.variantes = self._gerar_variantes()
        self.melhorias = {}
        self.estradas = set()
        self.rios = set()
        self._gerar_rios()

    def _campo_ruido(self, suavizacoes=5):
        campo = [[self.random.random() for _ in range(self.largura)] for _ in range(self.altura)]
        for _ in range(suavizacoes):
            novo = [[0.0] * self.largura for _ in range(self.altura)]
            for y in range(self.altura):
                for x in range(self.largura):
                    total = 0.0; qtd = 0
                    for dy in (-1,0,1):
                        for dx in (-1,0,1):
                            nx = (x + dx) % self.largura
                            ny = min(self.altura-1, max(0, y+dy))
                            total += campo[ny][nx]; qtd += 1
                    novo[y][x] = total / qtd
            campo = novo
        return campo

    def gerar_mapa(self):
        total = self.largura * self.altura
        quotas = {}; usados = 0
        for terreno in ['Água','Montanha','Deserto','Neve']:
            q = round(total * self.percentuais[terreno] / 100)
            quotas[terreno] = q; usados += q
        quotas['Grama'] = max(0, total-usados)
        oceano=self._campo_ruido(7); montanha=self._campo_ruido(4); deserto=self._campo_ruido(5); neve=self._campo_ruido(3)
        mapa=[[None for _ in range(self.largura)] for _ in range(self.altura)]
        livres={(x,y) for y in range(self.altura) for x in range(self.largura)}
        def escolher(qtd, score):
            candidatos=sorted(livres,key=lambda p:score(*p),reverse=True)
            escolhidos=candidatos[:min(qtd,len(candidatos))]
            for p in escolhidos: livres.remove(p)
            return escolhidos
        for x,y in escolher(quotas['Água'],lambda x,y:oceano[y][x]): mapa[y][x]='Água'
        def score_neve(x,y):
            lat=y/max(1,self.altura-1); return abs(lat-.5)*3.6+neve[y][x]*.45
        for x,y in escolher(quotas['Neve'],score_neve): mapa[y][x]='Neve'
        def score_montanha(x,y):
            vals=[]
            for dx,dy in VIZINHOS_4:
                nx=(x+dx)%self.largura; ny=min(self.altura-1,max(0,y+dy)); vals.append(montanha[ny][nx])
            r=montanha[y][x]; return r+abs(r-sum(vals)/len(vals))*.7
        for x,y in escolher(quotas['Montanha'],score_montanha): mapa[y][x]='Montanha'
        def score_deserto(x,y):
            lat=y/max(1,self.altura-1); d=abs(lat-.5); faixa=max(0.0,1.0-abs(d-.22)*3.0); return deserto[y][x]*1.2+faixa*.7
        for x,y in escolher(quotas['Deserto'],score_deserto): mapa[y][x]='Deserto'
        for x,y in livres: mapa[y][x]='Grama'
        return mapa

    def _classificar_aguas(self):
        terra=[]; agua=[]
        for y in range(self.altura):
            for x in range(self.largura):
                (agua if self.tiles[y][x]=='Água' else terra).append((x,y))
        fila=deque(); dist={}
        for x,y in terra:
            for dx,dy in VIZINHOS_8:
                nx,ny=x+dx,y+dy
                if self.dentro(nx,ny) and self.tiles[ny][nx]=='Água' and (nx,ny) not in dist:
                    dist[(nx,ny)]=1; fila.append((nx,ny))
        while fila:
            x,y=fila.popleft(); d=dist[(x,y)]
            if d>=2: continue
            for dx,dy in VIZINHOS_8:
                nx,ny=x+dx,y+dy
                if self.dentro(nx,ny) and self.tiles[ny][nx]=='Água' and (nx,ny) not in dist:
                    dist[(nx,ny)]=d+1; fila.append((nx,ny))
        for x,y in agua: self.tiles[y][x]='Água Rasa' if dist.get((x,y),99)<=2 else 'Água Profunda'

    def _gerar_variantes(self):
        variantes={}
        for y in range(self.altura):
            for x in range(self.largura):
                opcoes=VARIANTES_TERRENO.get(self.tiles[y][x],[])
                if not opcoes: continue
                total=sum(o['peso'] for o in opcoes); sorteio=self.random.uniform(0,total); acc=0; escolhido=opcoes[0]
                for opcao in opcoes:
                    acc += opcao['peso']
                    if sorteio<=acc: escolhido=opcao; break
                if escolhido.get('nome'): variantes[(x,y)]=escolhido
        return variantes

    def dentro(self,x,y): return 0<=x<self.largura and 0<=y<self.altura
    def terreno(self,x,y): return self.tiles[y][x] if self.dentro(x,y) else None
    def variante_em(self,x,y): return self.variantes.get((x,y))
    def melhoria_em(self,x,y): return self.melhorias.get((x,y))
    def tem_estrada(self,x,y): return (x,y) in self.estradas
    def construir_estrada(self,x,y):
        if not self.passavel(x,y) or (x,y) in self.estradas: return False
        self.estradas.add((x,y)); return True

    def _aresta_rio(self,a,b): return normalizar_aresta(a,b)
    def tem_rio_entre(self,a,b): return self._aresta_rio(a,b) in self.rios
    def tile_adjacente_rio(self,x,y):
        for dx,dy in VIZINHOS_4:
            nx,ny=x+dx,y+dy
            if self.dentro(nx,ny) and self.tem_rio_entre((x,y),(nx,ny)): return True
        return False

    def _tiles_costeiros(self):
        costeiros=[]
        for y in range(self.altura):
            for x in range(self.largura):
                if self.terreno(x,y) not in PASSAVEIS_TERRA: continue
                for dx,dy in VIZINHOS_4:
                    nx,ny=x+dx,y+dy
                    if self.dentro(nx,ny) and self.terreno(nx,ny)=='Água Rasa':
                        costeiros.append((x,y)); break
        return costeiros

    def _rota_rio_ate_mar(self, origem, destinos):
        permitidos=set(CONFIG_RIOS.get('terrenos_percurso',['Grama']))
        alvo=set(destinos)
        fila=[(0.0, origem)]
        custo={origem:0.0}; anterior={origem:None}
        while fila:
            _, atual=heapq.heappop(fila)
            if atual in alvo:
                caminho=[]; p=atual
                while p is not None:
                    caminho.append(p); p=anterior[p]
                caminho.reverse(); return caminho
            x,y=atual
            viz=list(VIZINHOS_4); self.random.shuffle(viz)
            for dx,dy in viz:
                prox=(x+dx,y+dy)
                if not self.dentro(*prox) or self.terreno(*prox) not in permitidos: continue
                # leve ruído produz meandros, mas ainda favorece rotas curtas.
                novo=custo[atual]+1.0+self.random.random()*0.35
                if novo < custo.get(prox, 1e18):
                    custo[prox]=novo; anterior[prox]=atual; heapq.heappush(fila,(novo,prox))
        return []

    def _gerar_rios(self):
        area=self.largura*self.altura
        qtd=max(1, round(area/1000*CONFIG_RIOS.get('densidade_por_1000_tiles',5)))
        costeiros=self._tiles_costeiros()
        nascentes=[(x,y) for y in range(self.altura) for x in range(self.largura) if self.terreno(x,y) in CONFIG_RIOS.get('terrenos_nascente',['Grama'])]
        if not costeiros or not nascentes: return
        self.random.shuffle(nascentes)
        criados=0
        for origem in nascentes:
            if criados>=qtd: break
            # evita rios minúsculos escolhendo uma costa não imediatamente adjacente.
            alvos=[c for c in costeiros if abs(c[0]-origem[0])+abs(c[1]-origem[1])>=CONFIG_RIOS.get('comprimento_minimo',4)]
            if not alvos: continue
            # reduz custo escolhendo costas relativamente próximas da origem.
            alvos=sorted(alvos,key=lambda c:abs(c[0]-origem[0])+abs(c[1]-origem[1]))[:max(20,min(120,len(alvos)))]
            rota=self._rota_rio_ate_mar(origem,alvos)
            if len(rota)<CONFIG_RIOS.get('comprimento_minimo',4): continue
            novas=[]
            for a,b in zip(rota,rota[1:]): novas.append(self._aresta_rio(a,b))
            fim=rota[-1]
            mares=[]
            for dx,dy in VIZINHOS_4:
                m=(fim[0]+dx,fim[1]+dy)
                if self.dentro(*m) and self.terreno(*m)=='Água Rasa': mares.append(m)
            if not mares: continue
            novas.append(self._aresta_rio(fim,self.random.choice(mares)))
            self.rios.update(novas); criados += 1

    def rendimentos_base_tile(self,x,y):
        base=dict(RENDIMENTOS_TERRENO.get(self.terreno(x,y),{}))
        for r in ('alimento','producao','ouro','ciencia','fe'): base.setdefault(r,0)
        return base

    def bonus_melhoria_tile(self,x,y):
        melhoria=self.melhoria_em(x,y)
        if not melhoria: return {k:0 for k in ('alimento','producao','ouro','ciencia','fe')}, []
        bonus={k:0 for k in ('alimento','producao','ouro','ciencia','fe')}; fontes=[]
        for recurso,v in MELHORIAS.get(melhoria,{}).get('bonus',{}).items(): bonus[recurso]+=v
        fontes.append(melhoria)
        variante=self.variante_em(x,y)
        if variante and melhoria in variante.get('melhorias_ativadoras',[]):
            for recurso,v in variante.get('modificadores',{}).items(): bonus[recurso]+=v
            fontes.append(variante['nome'])
        if melhoria=='Fazenda' and self.tile_adjacente_rio(x,y):
            bonus['alimento'] += 1; fontes.append('Rio')
        return bonus, fontes

    def passavel(self,x,y): return self.terreno(x,y) in PASSAVEIS_TERRA
    def passavel_mar(self,x,y): return self.terreno(x,y) in PASSAVEIS_MAR
    def passavel_mar_raso(self,x,y): return self.terreno(x,y) in PASSAVEIS_MAR_RASO
    def passavel_para(self,x,y,dominio='terra'):
        if dominio=='mar': return self.passavel_mar(x,y)
        if dominio=='mar_raso': return self.passavel_mar_raso(x,y)
        return self.passavel(x,y)

    def construir_melhoria(self,x,y,tipo):
        if not self.passavel(x,y) or (x,y) in self.melhorias: return False
        self.melhorias[(x,y)]=tipo; return True

    def encontrar_posicao_inicial(self):
        cx,cy=self.largura//2,self.altura//2
        if self.passavel(cx,cy): return cx,cy
        fila=deque([(cx,cy)]); vistos={(cx,cy)}
        while fila:
            x,y=fila.popleft()
            for dx,dy in VIZINHOS_8:
                nx,ny=x+dx,y+dy
                if not self.dentro(nx,ny) or (nx,ny) in vistos: continue
                if self.passavel(nx,ny): return nx,ny
                vistos.add((nx,ny)); fila.append((nx,ny))
        self.tiles[cy][cx]='Grama'; return cx,cy

    def custo_movimento(self, origem, destino, dominio='terra'):
        # Estrada é uma infraestrutura terrestre. Entrar em um tile de estrada custa 50%.
        if dominio=='terra' and self.tem_estrada(*destino): return 0.5
        return 1.0

    def caminho(self, origem, destino, dominio='terra'):
        if origem==destino: return []
        if not self.passavel_para(destino[0],destino[1],dominio): return []
        # Dijkstra: estradas tornam a melhor rota potencialmente diferente da rota mais curta em tiles.
        fila=[(0.0,origem)]; custo={origem:0.0}; anteriores={origem:None}
        while fila:
            atual_custo,atual=heapq.heappop(fila)
            if atual==destino: break
            if atual_custo>custo.get(atual,1e18): continue
            x,y=atual
            for dx,dy in VIZINHOS_8:
                prox=(x+dx,y+dy)
                if not self.dentro(*prox) or not self.passavel_para(*prox,dominio): continue
                novo=atual_custo+self.custo_movimento(atual,prox,dominio)
                if novo < custo.get(prox,1e18)-1e-9:
                    custo[prox]=novo; anteriores[prox]=atual; heapq.heappush(fila,(novo,prox))
        if destino not in anteriores: return []
        caminho=[]; atual=destino
        while atual!=origem:
            caminho.append(atual); atual=anteriores[atual]
        caminho.reverse(); return caminho
