cjson = require "cjson"
ips = {}
charset = {}
-- qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890
for i = 48,  57 do table.insert(charset, string.char(i)) end
for i = 65,  90 do table.insert(charset, string.char(i)) end
for i = 97, 122 do table.insert(charset, string.char(i)) end


function randomString(size)
	local res = ''
	for i = 1, size do
		res = res .. charset[math.random(1, #charset)]
	end
	return res
end


function randomIp()
    res = ''
    for i = 1, 4 do
        res = res .. tostring(math.random(1,255))
        if i < 4 then
            res = res .. '.'
        end
    end
    return res
end


function randomJson()
    local data = {}
    for i = 1, 10 do
        data[randomString(10)] = randomString(10)
    end
    return cjson.encode(data)
end


for i = 1, 10000 do
    table.insert(ips, randomIp())
end


function init()
    local socket = require('socket')
    math.randomseed(socket.gettime())
end


function done(summary, latency, requests)
    local http = require("socket.http")
    local url =
        wrk.scheme .. '://' ..
        wrk.host .. ':' ..
        wrk.port .. '/_debug/reset'
    http.request{
        url = url,
        method = 'POST'
    }

    io.write("------------------------------\n")
    for _, p in pairs({10, 25, 50, 75, 90, 95, 99, 99.9 }) do
        local n = latency:percentile(p) / 1000
        io.write(string.format("%g:\t%d ms\n", p, n))
    end
end


-- req_cnt = 0
function request()
    local ip = ips[math.random(1, #ips)]
    local x = math.random(100)
    --[[ req_cnt = req_cnt + 1

    if req_cnt == 1 then
        return wrk.format('POST', '/_debug/reset')
    end
    --]]

    if x < 10 then
        return wrk.format('POST', '/ip/' .. ip, nil, randomJson())
    elseif x < 25 then
        return wrk.format('DELETE', '/ip/' .. ip)
    else
        return wrk.format('GET', '/ip/' .. ip)
    end

end

