import asyncio
from aiohttp import web
import uvloop
from pymongo import MongoClient
from pymongo.database import Database
import motor.motor_asyncio
import json
from functools import lru_cache
from multiprocessing import Process
import sys
import japronto
import sanic
import sanic.response
import sanic.request


engine = 'aio'
dbhost = '127.0.0.1'
workers = 4
if len(sys.argv) > 1:
    workers = int(sys.argv[1])
if len(sys.argv) > 2:
    engine = sys.argv[2]
if len(sys.argv) > 3:
    dbhost = sys.argv[3]


make_response = {
    'aio': lambda req, body: web.Response(body=json.dumps(body)),
    'jap': lambda req, body: req.Response(text=json.dumps(body)),
    'san': lambda req, body: sanic.response.json(body),
}[engine]

get_param = {
    'aio': lambda req, name, kwargs: req.match_info[name],
    'jap': lambda req, name, kwargs: req.match_dict[name],
    'san': lambda req, name, kwargs: kwargs[name],
}[engine]

get_json_body = {
    'aio': lambda req: req.json(),
    'jap': lambda req: req.json,
    'san': lambda req: req.json,
}[engine]

make_app = {
    'aio': lambda: web.Application(),
    'jap': lambda: japronto.Application(),
    'san': lambda: sanic.Sanic(),
}[engine]

add_route = {
    'aio': lambda app, method, url, handler: app.router.add_route(method, url, handler),
    'jap': lambda app, method, url, handler: app.router.add_route(url, handler, methods=[method]),
    'san': lambda app, method, url, handler: app.router.add(url.replace('{', '<').replace('}', '>'), [method], handler)
}[engine]

run_app = {
    'aio': lambda app, host, port, reuse_port: web.run_app(app, host=host, port=port, reuse_port=reuse_port),
    'jap': lambda app, host, port, reuse_port: app.run(host=host, port=port, worker_num=workers),
    'san': lambda app, host, port, reuse_port: app.run(host=host, port=port, workers=workers, debug=False, access_log=False),
}[engine]


@lru_cache(maxsize=128)
def db() -> Database:
    # return motor.motor_asyncio.AsyncIOMotorClient(dbhost).test
    return MongoClient(dbhost).test


# async def get_ip(request, **kwargs):
def get_ip(request: web.Request, **kwargs):
    ip = get_param(request, 'ip', kwargs)
    # info = await db().ip_data.find_one(ip)
    info = db().ip_data.find_one(ip)
    info = info or {}
    return make_response(request, info)


async def post_ip(request: web.Request, **kwargs):
    ip = get_param(request, 'ip', kwargs)
    json_body = get_json_body(request)
    if asyncio.iscoroutine(json_body):
        json_body = await json_body
    doc = {
        '_id': ip,
        **json_body
    }
    # await db().ip_data.update_one({'_id': ip}, {'$set': doc}, upsert=True)
    db().ip_data.update_one({'_id': ip}, {'$set': doc}, upsert=True)
    return make_response(request, body=json.dumps({}))


# async def delete_ip(request, **kwargs):
def delete_ip(request: web.Request, **kwargs):
    ip = get_param(request, 'ip', kwargs)
    # await db().ip_data.delete_one({'_id': ip})
    db().ip_data.delete_one({'_id': ip})
    return make_response(request, body=json.dumps({}))


async def reset(request):
    import time
    start = time.time()
    # await db().ip_data.drop()
    db().ip_data.drop()
    dt = time.time() - start
    print(f'Dropped db in {dt * 1e3:.02f} ms')
    return make_response(request, '')


def main():
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    app = make_app()
    add_route(app, 'GET', '/ip/{ip}', get_ip)
    add_route(app, 'POST', '/ip/{ip}', post_ip)
    add_route(app, 'DELETE', '/ip/{ip}', delete_ip)
    add_route(app, 'POST', '/_debug/reset', reset)
    run_app(app, host='0', port=10080, reuse_port=True)


if __name__ == '__main__':
    if engine == 'aio':
        procs = [Process(target=main) for _ in range(workers)]
        [p.start() for p in procs]
        [p.join() for p in procs]
    elif engine in ('jap', 'san'):
        main()

