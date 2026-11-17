return function(conf, ctx)
    local core = require("apisix.core")
    local http = require("resty.http")
    local args = ngx.var.args or ""
    local uri = ngx.var.uri or "/"
    local path = string.gsub(uri, "^/api", "")
    local query_args = ngx.req.get_uri_args()
    local query_count = 0
    for _ in pairs(query_args) do
        query_count = query_count + 1
    end
    local headers = ngx.req.get_headers()
    local header_count = 0
    for _ in pairs(headers) do
        header_count = header_count + 1
    end
    ngx.req.read_body()
    local body = ngx.req.get_body_data() or ""
    local user_agent = headers["user-agent"] or ""
    local payload = core.json.encode({
        path_length = #path,
        query_length = #args,
        query_param_count = query_count,
        header_count = math.min(header_count, 8),
        user_agent_length = #user_agent,
        request_body_bytes = #body,
        interarrival_ms = 0,
        requests_last_10s = 1
    })
    local client = http.new()
    client:set_timeout(1000)
    local response, err = client:request_uri("http://ai-engine:8000/score", {
        method = "POST",
        body = payload,
        headers = { ["Content-Type"] = "application/json" }
    })
    if not response then
        ngx.log(ngx.ERR, "AI security service unavailable: ", err or "unknown error")
        return ngx.exit(503)
    end
    if response.status ~= 200 then
        ngx.log(ngx.ERR, "AI security service returned status ", response.status)
        return ngx.exit(503)
    end
    local decision, decode_err = core.json.decode(response.body)
    if not decision then
        ngx.log(ngx.ERR, "Invalid AI security response: ", decode_err or "unknown error")
        return ngx.exit(503)
    end
    ngx.header["X-AI-Decision"] = decision.decision
    ngx.header["X-AI-Score"] = tostring(decision.suspicious_probability or "")
    if decision.decision == "BLOCK" then
        ngx.status = 403
        ngx.say("Request blocked by AI security policy")
        return ngx.exit(403)
    end
    if decision.decision == "RATE LIMIT" then
        ngx.header["Retry-After"] = "10"
        ngx.status = 429
        ngx.say("Request rate limited by AI security policy")
        return ngx.exit(429)
    end
end
