async def test_list_and_filter(client, make_endpoint, fire, receiver, drain):
    ok = await make_endpoint(url="https://ok.example.com/")
    bad = await make_endpoint(url="https://bad.example.com/")
    receiver.respond(400)  # both fail; then fix one and replay it
    await fire()
    await drain()

    all_ = (await client.get("/api/deliveries")).json()
    assert len(all_) == 2
    assert {d["status"] for d in all_} == {"failed"}

    ok_delivery = (await client.get("/api/deliveries", params={"endpoint_id": ok["id"]})).json()
    assert [d["endpoint_url"] for d in ok_delivery] == ["https://ok.example.com/"]
    receiver.respond(200)
    await client.post(f"/api/deliveries/{ok_delivery[0]['id']}/replay")
    await drain()

    failed = (await client.get("/api/deliveries", params={"status": "failed"})).json()
    assert [d["endpoint_id"] for d in failed] == [bad["id"]]
    assert (await client.get("/api/deliveries", params={"status": "nope"})).status_code == 422


async def test_detail_has_payload_and_attempt_log(client, make_endpoint, fire, receiver, drain):
    await make_endpoint()
    receiver.respond(503, 200)
    payload = (await fire()).json()["event"]["payload"]
    await drain()

    [summary] = (await client.get("/api/deliveries")).json()
    assert summary["attempt_count"] == 2
    assert summary["max_attempts"] == 5
    assert summary["event_type"] == "campaign_updated"

    detail = (await client.get(f"/api/deliveries/{summary['id']}")).json()
    assert detail["payload"] == payload
    assert [a["response_status"] for a in detail["attempts"]] == [503, 200]
    assert detail["attempts"][0]["error"] == "HTTP 503"
    assert detail["attempts"][0]["response_body"] == "nope"


async def test_unknown_delivery(client):
    r = await client.get("/api/deliveries/dlv_nope")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"
