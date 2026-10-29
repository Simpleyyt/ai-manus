#!/usr/bin/env python3
# mini_manus.py — agente mínimo do guia prático (60 linhas)
# Requisitos: pip install openai requests, container da seção 5, SearXNG da seção 6
import json, os, subprocess, requests
from openai import OpenAI

client = OpenAI(base_url=os.getenv('LLM_BASE_URL', 'http://localhost:11434/v1'),
                api_key=os.getenv('LLM_API_KEY', 'ollama'))
MODEL = os.getenv('LLM_MODEL', 'gpt-oss:20b')
BOX = 'agent-sandbox'

SYSTEM = '''Você é um agente autônomo com um computador Linux (/workspace).
Escreva o plano em /workspace/todo.md e atualize-o a cada etapa concluída.
Use run_shell e run_python para agir e salve os resultados em arquivos.
Se um comando falhar, leia o erro e mude a abordagem.
Ao terminar, chame finish com o resumo e os caminhos dos arquivos.'''

def tool(name, desc, props):
    return {'type': 'function', 'function': {
        'name': name, 'description': desc,
        'parameters': {'type': 'object', 'properties': props,
                       'required': list(props)}}}

S = {'type': 'string'}
TOOLS = [tool('run_shell', 'Executa bash no sandbox', {'cmd': S}),
         tool('run_python', 'Executa Python no sandbox', {'code': S}),
         tool('web_search', 'Busca na web', {'query': S}),
         tool('finish', 'Encerra a tarefa', {'summary': S})]

def trim(s, n=4000):
    return s if len(s) <= n else s[:n // 2] + '\n[...cortado...]\n' + s[-n // 2:]

def docker(args, stdin=None):
    r = subprocess.run(['docker', 'exec', *args], input=stdin,
                       capture_output=True, text=True, timeout=180)
    return trim(r.stdout + r.stderr) or '(sem saída)'

def search(q):
    try:
        res = requests.get('http://localhost:8080/search', timeout=30,
                           params={'q': q, 'format': 'json'}).json()['results']
        lines = [x['title'] + ' | ' + x['url'] + ' | ' + x.get('content', '')[:300]
                 for x in res[:6]]
        return '\n'.join(lines) or '(nada encontrado)'
    except Exception as e:
        return f'Busca falhou: {e}'

ACTIONS = {
    'run_shell': lambda a: docker([BOX, 'bash', '-lc', a['cmd']]),
    'run_python': lambda a: docker(['-i', BOX, 'python3', '-'], a['code']),
    'web_search': lambda a: search(a['query']),
}

def run(task, max_steps=30):
    msgs = [{'role': 'system', 'content': SYSTEM},
            {'role': 'user', 'content': task}]
    for _ in range(max_steps):
        m = client.chat.completions.create(
            model=MODEL, messages=msgs, tools=TOOLS).choices[0].message
        msg = {'role': 'assistant', 'content': m.content or ''}
        if m.tool_calls:
            msg['tool_calls'] = [
                {'id': c.id, 'type': 'function',
                 'function': {'name': c.function.name,
                              'arguments': c.function.arguments}}
                for c in m.tool_calls]
        msgs.append(msg)
        if not m.tool_calls:
            return m.content
        for c in m.tool_calls:
            name = c.function.name
            try:
                args = json.loads(c.function.arguments or '{}')
                if name == 'finish':
                    return args['summary']
                obs = ACTIONS[name](args) if name in ACTIONS else 'ferramenta desconhecida'
            except Exception as e:
                obs = 'ERRO: ' + str(e)
            msgs.append({'role': 'tool', 'tool_call_id': c.id, 'content': obs})
    return 'Limite de passos atingido.'

if __name__ == '__main__':
    print(run(input('Tarefa: ')))
