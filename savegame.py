import json
import os

SAVE_VERSION = 2
ARQUIVO_SAVE_PADRAO = os.path.join(os.path.dirname(__file__), 'tlc_civ_save.json')


def _pt(p):
    return [int(p[0]), int(p[1])]


def _edge(e):
    return [_pt(e[0]), _pt(e[1])]


def _set_points(valores):
    return [_pt(v) for v in sorted(valores)]


def serializar_jogo(jogo):
    mundo = jogo.mundo
    jogadores = []
    for j in jogo.jogadores:
        jogadores.append({
            'id': j.id,
            'uid': j.uid,
            'nome': j.nome,
            'cor': list(j.cor),
            'civilizacao': j.civilizacao,
            'humano': j.humano,
            'dificuldade': j.dificuldade,
            'tipo': j.tipo, 'lider_nome': j.lider_nome, 'lider_genero': j.lider_genero,
            'contatos_diplomaticos': sorted(j.contatos_diplomaticos),
            'humor_relacoes': dict(j.humor_relacoes),
            'tecnologias': sorted(j.tecnologias),
            'politicas': sorted(j.politicas),
            'era': j.era,
            'pesquisa_atual': j.pesquisa_atual,
            'progresso_pesquisa': j.progresso_pesquisa,
            'ouro': j.ouro,
            'ciencia': j.ciencia,
            'fe': j.fe,
            'capital_id': j.capital_id,
            'explorado': _set_points(j.explorado),
            'visivel': _set_points(j.visivel),
            'modificadores_temporarios': j.modificadores_temporarios,
        })

    cidades = []
    for c in jogo.cidades:
        cidades.append({
            'id': c.id, 'nome': c.nome, 'x': c.x, 'y': c.y, 'dono_id': c.dono_id,
            'construcoes': list(c.construcoes),
            'producao_tipo': c.producao_tipo, 'producao_nome': c.producao_nome,
            'custo_producao_atual': c.custo_producao_atual,
            'producao_por_turno_inicio': c.producao_por_turno_inicio,
            'turnos_producao_total': c.turnos_producao_total,
            'turnos_producao_restantes': c.turnos_producao_restantes,
            'populacao': c.populacao, 'alimento': c.alimento, 'producao': c.producao,
            'lealdade': c.lealdade, 'felicidade': c.felicidade, 'em_revolta': c.em_revolta,
            'capital': c.capital,
            'melhorias': [list(m) for m in c.melhorias],
            'raio_territorio': c.raio_territorio,
            'tiles_territorio': _set_points(c.tiles_territorio),
            'limites_lealdade_atingidos': sorted(c.limites_lealdade_atingidos),
            'modificadores_temporarios': c.modificadores_temporarios,
        })

    unidades = []
    for u in jogo.unidades:
        unidades.append({
            'id': u.id, 'tipo': u.tipo, 'x': u.x, 'y': u.y, 'dono_id': u.dono_id,
            'movimento': u.movimento, 'fortificada': u.fortificada,
            'melhorias_construidas': u.melhorias_construidas,
            'embarcada_em_id': u.embarcada_em.id if u.embarcada_em else None,
            'carga_ids': [x.id for x in u.carga],
            'vida': u.vida, 'experiencia': u.experiencia, 'nivel': u.nivel,
            'modificadores_temporarios': u.modificadores_temporarios,
        })

    acampamentos = [
        {'id': a.id, 'x': a.x, 'y': a.y, 'dono_id': a.dono_id, 'ativo': a.ativo}
        for a in jogo.acampamentos_barbaros
    ]

    variantes = []
    for (x, y), valor in mundo.variantes.items():
        variantes.append({'x': x, 'y': y, 'valor': valor})

    sistemas = []
    for s in mundo.sistemas_rios:
        sistemas.append({
            'id': s['id'],
            'principal': [_pt(v) for v in s['principal']],
            'afluentes': [[_pt(v) for v in af] for af in s['afluentes']],
            'nascente': _pt(s['nascente']) if s.get('nascente') else None,
            'desague': s.get('desague'),
            'arestas': [_edge(e) for e in s.get('arestas', [])],
            'vertices': [_pt(v) for v in s.get('vertices', [])],
        })

    return {
        'save_version': SAVE_VERSION,
        'game_version': '0.21',
        'configuracao': jogo.configuracao,
        'turno': jogo.turno,
        'rng_state': jogo.random.getstate(),
        'ano': jogo.calendario.ano,
        'id_counters': jogo.gerador_ids.exportar(),
        'jogadores': jogadores,
        'cidades': cidades,
        'unidades': unidades,
        'acampamentos_barbaros': acampamentos,
        'mundo': {
            'largura': mundo.largura, 'altura': mundo.altura,
            'percentuais': mundo.percentuais, 'seed': mundo.seed,
            'densidade_rios': mundo.densidade_rios,
            'tiles': mundo.tiles,
            'variantes': variantes,
            'melhorias': [{'x': x, 'y': y, 'tipo': tipo} for (x, y), tipo in mundo.melhorias.items()],
            'estradas': _set_points(mundo.estradas),
            'rios': [_edge(e) for e in mundo.rios],
            'sistemas_rios': sistemas,
            'rios_criados': mundo.rios_criados,
            'afluentes_criados': mundo.afluentes_criados,
        },
    }


def salvar_jogo(jogo, caminho=ARQUIVO_SAVE_PADRAO):
    dados = serializar_jogo(jogo)
    os.makedirs(os.path.dirname(caminho) or '.', exist_ok=True)
    with open(caminho, 'w', encoding='utf-8') as arq:
        json.dump(dados, arq, ensure_ascii=False, indent=2)
    return caminho


def ler_save(caminho=ARQUIVO_SAVE_PADRAO):
    with open(caminho, 'r', encoding='utf-8') as arq:
        dados = json.load(arq)
    versao = int(dados.get('save_version', 0))
    if versao not in (1, SAVE_VERSION):
        raise ValueError(f'Save incompatível: versão {versao}; esperado 1 ou {SAVE_VERSION}.')
    return dados


def existe_save(caminho=ARQUIVO_SAVE_PADRAO):
    return os.path.isfile(caminho)
