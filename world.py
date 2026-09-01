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
    def __init__(self, largura, altura, percentuais, seed=None, densidade_rios='Médio'):
        self.largura = largura
        self.altura = altura
        self.percentuais = percentuais
        self.seed = seed if seed is not None else random.SystemRandom().randrange(1, 2_147_483_647)
        self.densidade_rios = densidade_rios if densidade_rios in CONFIG_RIOS.get('densidades', {}) else 'Médio'
        self.random = random.Random(self.seed)
        self.tiles = self.gerar_mapa()
        self._classificar_aguas()
        self.variantes = self._gerar_variantes()
        self.melhorias = {}
        self.estradas = set()
        self.rios = set()
        # Hidrografia organizada por bacias. Cada aresta pertence a uma única bacia.
        self.sistemas_rios = []
        self.rio_bacia_por_aresta = {}
        self.rios_criados = 0
        self.afluentes_criados = 0
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

    def _aresta_rio(self, a, b):
        """Aresta de rio entre vértices da grade (cantos dos tiles)."""
        return normalizar_aresta(a, b)

    def _bordas_tile(self, x, y):
        """Quatro bordas do tile, representadas por pares de vértices da grade."""
        return (
            self._aresta_rio((x, y), (x + 1, y)),
            self._aresta_rio((x + 1, y), (x + 1, y + 1)),
            self._aresta_rio((x, y + 1), (x + 1, y + 1)),
            self._aresta_rio((x, y), (x, y + 1)),
        )

    def _borda_compartilhada_tiles(self, a, b):
        ax, ay = a; bx, by = b
        dx, dy = bx - ax, by - ay
        if abs(dx) + abs(dy) != 1:
            return None
        if dx == 1:
            return self._aresta_rio((ax + 1, ay), (ax + 1, ay + 1))
        if dx == -1:
            return self._aresta_rio((ax, ay), (ax, ay + 1))
        if dy == 1:
            return self._aresta_rio((ax, ay + 1), (ax + 1, ay + 1))
        return self._aresta_rio((ax, ay), (ax + 1, ay))

    def tem_rio_entre(self, a, b):
        borda = self._borda_compartilhada_tiles(a, b)
        return bool(borda and borda in self.rios)

    def tile_adjacente_rio(self, x, y):
        return any(borda in self.rios for borda in self._bordas_tile(x, y))

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

    def _distancias_ate_costa(self, costeiros):
        permitidos = set(CONFIG_RIOS.get('terrenos_percurso', ['Grama', 'Deserto', 'Neve']))
        fila = deque(); dist = {}
        for c in costeiros:
            if self.terreno(*c) in permitidos:
                dist[c] = 0; fila.append(c)
        while fila:
            x, y = fila.popleft()
            for dx, dy in VIZINHOS_4:
                n=(x+dx,y+dy)
                if not self.dentro(*n) or n in dist or self.terreno(*n) not in permitidos:
                    continue
                dist[n]=dist[(x,y)]+1; fila.append(n)
        return dist

    def _tiles_ao_lado_aresta_grade(self, a, b):
        """Retorna tiles que encostam numa aresta da grade de vértices."""
        (x1,y1),(x2,y2)=a,b
        tiles=[]
        if y1==y2:  # aresta horizontal
            x=min(x1,x2); y=y1
            for t in ((x,y-1),(x,y)):
                if self.dentro(*t): tiles.append(t)
        elif x1==x2:  # aresta vertical
            x=x1; y=min(y1,y2)
            for t in ((x-1,y),(x,y)):
                if self.dentro(*t): tiles.append(t)
        return tiles

    def _aresta_grade_permitida(self, a, b, aresta_final=None):
        if not (0 <= a[0] <= self.largura and 0 <= a[1] <= self.altura and
                0 <= b[0] <= self.largura and 0 <= b[1] <= self.altura):
            return False
        if abs(a[0]-b[0]) + abs(a[1]-b[1]) != 1:
            return False
        edge=self._aresta_rio(a,b)
        # A borda costeira é apenas o limite de chegada do rio.
        # Ela NÃO faz parte do curso: o último segmento termina antes dela,
        # evitando uma faixa azul desenhada sobre a divisa terra-mar.
        if aresta_final is not None and edge == aresta_final:
            return False
        adj=self._tiles_ao_lado_aresta_grade(a,b)
        permitidos=set(CONFIG_RIOS.get('terrenos_percurso',['Grama','Deserto','Neve']))
        # O curso terrestre deve correr entre/ao lado de terra e não acompanhar o mar.
        return bool(adj) and any(self.terreno(*t) in permitidos for t in adj) and not any(self.terreno(*t) in PASSAVEIS_MAR for t in adj)

    def _arestas_litorais(self):
        """Bordas exatas entre terra passável e Água Rasa, com o tile marinho do deságue."""
        saida=[]
        vistos=set()
        for y in range(self.altura):
            for x in range(self.largura):
                if self.terreno(x,y) not in PASSAVEIS_TERRA: continue
                for dx,dy in VIZINHOS_4:
                    mar=(x+dx,y+dy)
                    if not self.dentro(*mar) or self.terreno(*mar)!='Água Rasa': continue
                    edge=self._borda_compartilhada_tiles((x,y),mar)
                    if edge and edge not in vistos:
                        vistos.add(edge); saida.append((edge,(x,y),mar))
        return saida

    def _vertices_de_arestas(self, arestas):
        vertices=set()
        for a,b in arestas:
            vertices.add(a); vertices.add(b)
        return vertices

    def _vertices_proximos(self, vertices, raio):
        """Expande um conjunto de vértices por distância Chebyshev na grade."""
        if raio <= 0:
            return set(vertices)
        saida=set()
        for vx,vy in vertices:
            for dy in range(-raio, raio+1):
                for dx in range(-raio, raio+1):
                    nx,ny=vx+dx,vy+dy
                    if 0 <= nx <= self.largura and 0 <= ny <= self.altura:
                        saida.add((nx,ny))
        return saida

    def _vertices_outras_bacias(self, bacia_id=None):
        vertices=set()
        for sistema in self.sistemas_rios:
            if bacia_id is not None and sistema['id'] == bacia_id:
                continue
            vertices.update(sistema['vertices'])
        return vertices

    def _distancia_vertice_conjunto(self, vertice, conjunto):
        if not conjunto:
            return 10**9
        vx,vy=vertice
        return min(max(abs(vx-x),abs(vy-y)) for x,y in conjunto)

    def _cantos_tile(self, tile):
        x,y=tile
        return ((x,y),(x+1,y),(x,y+1),(x+1,y+1))

    def _mapa_distancias_litoral_vertices(self, bloqueados_vertices):
        """BFS multi-source na malha de vértices até pontos válidos de litoral.

        Retorna distância e opções de deságue por vértice costeiro. É recalculado
        por bacia porque a zona de proteção muda conforme novos sistemas surgem.
        """
        dist={}; fila=deque(); desagues_por_vertice={}
        for info in self._arestas_litorais():
            aresta_final, terra, mar = info
            if any(v in bloqueados_vertices for v in aresta_final):
                continue
            dado={'aresta':aresta_final,'terra':terra,'mar':mar}
            for v in aresta_final:
                if v in bloqueados_vertices:
                    continue
                desagues_por_vertice.setdefault(v,[]).append(dado)
                if v not in dist:
                    dist[v]=0; fila.append(v)
        while fila:
            atual=fila.popleft()
            for dx,dy in VIZINHOS_4:
                prox=(atual[0]+dx,atual[1]+dy)
                if prox in dist or prox in bloqueados_vertices:
                    continue
                if not self._aresta_grade_permitida(atual,prox,None):
                    continue
                dist[prox]=dist[atual]+1
                fila.append(prox)
        return dist, desagues_por_vertice

    def _rota_descendo_distancia(self, origem, dist, alvo=None, proibidos=None):
        """Segue sempre para um vértice de distância menor, com curvas suaves."""
        proibidos=proibidos or set()
        if origem not in dist or origem in proibidos:
            return []
        rota=[origem]; atual=origem; direcao_anterior=None
        limite=(self.largura+self.altura)*4
        for _ in range(limite):
            if alvo is not None and atual==alvo:
                return rota
            if alvo is None and dist.get(atual,0)==0:
                return rota
            atual_d=dist.get(atual)
            candidatos=[]
            for dx,dy in VIZINHOS_4:
                prox=(atual[0]+dx,atual[1]+dy)
                if prox in proibidos and prox != alvo:
                    continue
                if prox not in dist or dist[prox] >= atual_d:
                    continue
                if not self._aresta_grade_permitida(atual,prox,None):
                    continue
                direcao=(dx,dy)
                penalidade_curva=0 if direcao_anterior is None or direcao==direcao_anterior else 0.20
                candidatos.append((dist[prox]+penalidade_curva+self.random.random()*0.18,prox,direcao))
            if not candidatos:
                return []
            candidatos.sort(key=lambda item:item[0])
            # Entre as duas melhores opções, às vezes escolhe a segunda para dar
            # um meandro leve sem criar zigue-zague caótico.
            escolha=0
            if len(candidatos)>1 and self.random.random()<0.18:
                escolha=1
            _,prox,direcao=candidatos[escolha]
            rota.append(prox); atual=prox; direcao_anterior=direcao
        return []

    def _mapa_distancias_alvo(self, alvo, proibidos):
        """BFS do ponto de confluência para gerar um afluente eficientemente."""
        dist={alvo:0}; fila=deque([alvo])
        while fila:
            atual=fila.popleft()
            for dx,dy in VIZINHOS_4:
                prox=(atual[0]+dx,atual[1]+dy)
                if prox in dist or (prox in proibidos and prox != alvo):
                    continue
                if not self._aresta_grade_permitida(atual,prox,None):
                    continue
                dist[prox]=dist[atual]+1
                fila.append(prox)
        return dist

    def _fonte_longe_de_bacias(self, tile, vertices_existentes, distancia_min):
        return all(
            self._distancia_vertice_conjunto(canto, vertices_existentes) > distancia_min
            for canto in self._cantos_tile(tile)
        )

    def _registrar_sistema(self, sistema):
        sistema['arestas']=set(self._aresta_rio(a,b) for a,b in zip(sistema['principal'],sistema['principal'][1:]))
        sistema['vertices']=set(sistema['principal'])
        for af in sistema['afluentes']:
            sistema['arestas'].update(self._aresta_rio(a,b) for a,b in zip(af,af[1:]))
            sistema['vertices'].update(af)
        for edge in sistema['arestas']:
            self.rio_bacia_por_aresta[edge]=sistema['id']
        self.rios.update(sistema['arestas'])

    def _escolher_fonte_principal(self, fontes, dist_vertices, vertices_existentes, distancia_bacias, fontes_usadas, minimo):
        # Fontes mais interiores primeiro, com uma pequena janela aleatória.
        candidatos=[]
        for tile in fontes:
            if tile in fontes_usadas or not self._fonte_longe_de_bacias(tile,vertices_existentes,distancia_bacias):
                continue
            cantos=[c for c in self._cantos_tile(tile) if c in dist_vertices and dist_vertices[c]>=minimo]
            if cantos:
                melhor=max(dist_vertices[c] for c in cantos)
                candidatos.append((melhor,tile,cantos))
        if not candidatos:
            return None,None
        candidatos.sort(key=lambda item:item[0],reverse=True)
        janela=candidatos[:max(1,min(20,len(candidatos)//3+1))]
        _,tile,cantos=self.random.choice(janela)
        self.random.shuffle(cantos)
        cantos.sort(key=lambda c:dist_vertices[c],reverse=True)
        return tile,cantos

    def _escolher_fonte_afluente(self, sistema, alvo, dist_alvo, dist_costa, proibidos, fontes_usadas):
        terrenos_nascente=set(CONFIG_RIOS.get('terrenos_nascente',['Grama']))
        candidatos=[]
        for tile,d_costa in dist_costa.items():
            if tile in fontes_usadas or self.terreno(*tile) not in terrenos_nascente or d_costa<2:
                continue
            cantos=[c for c in self._cantos_tile(tile) if c in dist_alvo and c not in proibidos]
            if not cantos:
                continue
            # Não nasce colado ao principal/afluente já existente.
            dist_rota=min(dist_alvo[c] for c in cantos)
            if dist_rota<4:
                continue
            candidatos.append((dist_rota,d_costa,tile,cantos))
        if not candidatos:
            return None,None
        # Prefere tributários de comprimento moderado; evita atravessar metade do continente.
        candidatos.sort(key=lambda item:(abs(item[0]-7),-item[1]))
        janela=candidatos[:min(40,len(candidatos))]
        dist_rota,d_costa,tile,cantos=self.random.choice(janela)
        cantos.sort(key=lambda c:dist_alvo[c])
        return tile,cantos

    def _gerar_rios(self):
        """Gera bacias hidrográficas independentes e legíveis.

        Densidade controla o total aproximado de cursos visíveis. Esses cursos são
        agrupados em bacias: um principal com um único deságue + até 2 afluentes.
        Bacias distintas mantêm uma faixa de separação e nunca se conectam.
        """
        area=self.largura*self.altura
        fator=CONFIG_RIOS.get('densidades',{}).get(self.densidade_rios,10.0)
        escala=(area**0.5)/36.0
        qtd_cursos_alvo=max(1,int(round(fator*escala)))
        max_afluentes=int(CONFIG_RIOS.get('max_afluentes_por_rio',2))
        qtd_bacias_alvo=max(1,int((qtd_cursos_alvo+max_afluentes)//(max_afluentes+1)))
        cfg_dist=CONFIG_RIOS.get('distancia_min_bacias',2)
        distancia_bacias=int(cfg_dist.get(self.densidade_rios,2)) if isinstance(cfg_dist,dict) else int(cfg_dist)

        costeiros=self._tiles_costeiros()
        self.rios=set(); self.sistemas_rios=[]; self.rio_bacia_por_aresta={}
        self.desagues=[]; self.rios_principais=[]; self.afluentes=[]
        if not costeiros:
            self.rios_criados=0; self.afluentes_criados=0; return

        dist_costa=self._distancias_ate_costa(costeiros)
        minimo=int(CONFIG_RIOS.get('comprimento_minimo',5))
        terrenos_nascente=set(CONFIG_RIOS.get('terrenos_nascente',['Grama']))
        fontes=[p for p,d in dist_costa.items() if d>=minimo and self.terreno(*p) in terrenos_nascente]
        if not fontes:
            fontes=[p for p,d in dist_costa.items() if d>=max(2,minimo//2) and self.terreno(*p) in terrenos_nascente]
        fontes_usadas=set()

        # 1) PRINCIPAIS: cada novo sistema recebe uma zona exclusiva.
        falhas_seguidas=0
        while len(self.sistemas_rios)<qtd_bacias_alvo and falhas_seguidas<20:
            vertices_existentes=self._vertices_outras_bacias()
            bloqueados=self._vertices_proximos(vertices_existentes,distancia_bacias)
            dist_vertices, desagues_por_vertice=self._mapa_distancias_litoral_vertices(bloqueados)
            tile_fonte,cantos=self._escolher_fonte_principal(
                fontes,dist_vertices,vertices_existentes,distancia_bacias,fontes_usadas,minimo
            )
            if tile_fonte is None:
                break
            fontes_usadas.add(tile_fonte)
            rota=None; desague=None
            for origem in cantos:
                tentativa=self._rota_descendo_distancia(origem,dist_vertices,proibidos=bloqueados)
                if len(tentativa)<max(3,minimo):
                    continue
                fim=tentativa[-1]
                opcoes=desagues_por_vertice.get(fim,[])
                if not opcoes:
                    continue
                rota=tentativa; desague=self.random.choice(opcoes); break
            if not rota:
                falhas_seguidas+=1; continue

            sid=len(self.sistemas_rios)+1
            sistema={'id':sid,'principal':rota,'afluentes':[],'nascente':tile_fonte,
                     'desague':desague,'arestas':set(),'vertices':set()}
            self._registrar_sistema(sistema)
            self.sistemas_rios.append(sistema)
            self.desagues.append(desague); self.rios_principais.append(rota)
            falhas_seguidas=0

        # 2) AFLUENTES: distribui o restante da densidade entre as bacias.
        for idx,sistema in enumerate(self.sistemas_rios):
            principal=sistema['principal']
            if len(principal)<7:
                continue
            cursos_atuais=len(self.sistemas_rios)+sum(len(s['afluentes']) for s in self.sistemas_rios)
            faltam=max(0,qtd_cursos_alvo-cursos_atuais)
            bacias_restantes=max(1,len(self.sistemas_rios)-idx)
            qtd=min(max_afluentes,max(0,int((faltam+bacias_restantes-1)//bacias_restantes)))
            if qtd<=0:
                continue
            pontos_validos=list(principal[2:-2]); self.random.shuffle(pontos_validos)
            alvos_usados=[]
            for _ in range(qtd):
                alvo=None
                for candidato in pontos_validos:
                    if all(max(abs(candidato[0]-a[0]),abs(candidato[1]-a[1]))>=3 for a in alvos_usados):
                        alvo=candidato; break
                if alvo is None:
                    break
                alvos_usados.append(alvo); pontos_validos.remove(alvo)

                outras=self._vertices_outras_bacias(sistema['id'])
                bloqueados_outras=self._vertices_proximos(outras,distancia_bacias)
                existentes_mesma=set(sistema['vertices'])
                # Para chegar ao principal, o alvo é a única exceção.
                proibidos=set(bloqueados_outras) | (existentes_mesma-{alvo})
                dist_alvo=self._mapa_distancias_alvo(alvo,proibidos)
                tile_fonte,cantos=self._escolher_fonte_afluente(
                    sistema,alvo,dist_alvo,dist_costa,proibidos,fontes_usadas
                )
                if tile_fonte is None:
                    continue
                rota=None
                for origem in cantos:
                    tentativa=self._rota_descendo_distancia(origem,dist_alvo,alvo=alvo,proibidos=proibidos)
                    if len(tentativa)>=4 and tentativa[-1]==alvo:
                        rota=tentativa; break
                if not rota:
                    continue
                # Segurança: somente o último vértice pode pertencer ao sistema.
                if set(rota[:-1]) & sistema['vertices']:
                    continue
                edges=set(self._aresta_rio(a,b) for a,b in zip(rota,rota[1:]))
                if edges & self.rios:
                    continue
                sistema['afluentes'].append(rota)
                sistema['arestas'].update(edges); sistema['vertices'].update(rota)
                self.rios.update(edges)
                for e in edges:
                    self.rio_bacia_por_aresta[e]=sistema['id']
                self.afluentes.append(rota); fontes_usadas.add(tile_fonte)

        self.rios_criados=len(self.sistemas_rios)
        self.afluentes_criados=sum(len(s['afluentes']) for s in self.sistemas_rios)

    # ---------- consultas de bacias hidrográficas ----------
    def bacia_por_id(self, bacia_id):
        return next((s for s in self.sistemas_rios if s.get('id') == bacia_id), None)

    def bacia_do_tile(self, x, y):
        """Retorna a bacia que toca uma das bordas do tile, ou None."""
        ids=[]
        for borda in self._bordas_tile(x, y):
            bid=self.rio_bacia_por_aresta.get(borda)
            if bid is not None and bid not in ids:
                ids.append(bid)
        return ids[0] if ids else None

    def bacias_do_tile(self, x, y):
        ids=[]
        for borda in self._bordas_tile(x, y):
            bid=self.rio_bacia_por_aresta.get(borda)
            if bid is not None and bid not in ids:
                ids.append(bid)
        return ids

    def cidade_na_bacia(self, cidade):
        ids=set()
        for x,y in getattr(cidade, 'tiles_territorio', {(cidade.x,cidade.y)}):
            ids.update(self.bacias_do_tile(x,y))
        return min(ids) if ids else None

    def cidades_na_mesma_bacia(self, cidade_a, cidade_b):
        a=self.cidade_na_bacia(cidade_a); b=self.cidade_na_bacia(cidade_b)
        return a is not None and a == b

    def rio_principal_da_bacia(self, bacia_id):
        sistema=self.bacia_por_id(bacia_id)
        return list(sistema.get('principal', [])) if sistema else []

    def afluentes_da_bacia(self, bacia_id):
        sistema=self.bacia_por_id(bacia_id)
        return [list(x) for x in sistema.get('afluentes', [])] if sistema else []

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
