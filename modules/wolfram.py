from nio import MatrixRoom

from dors import command_hook, HookMessage, Jenny
import wolframalpha
import config
import re

unire = re.compile(r"\\:([0-9a-fA-F]{4})")
client = wolframalpha.Client(config.wolframalpha_apikey)


def fixaroo(m):
    txt = m.group(1)
    return chr(int(txt, 16))


@command_hook(['wolframalpha', 'wa'], help=".wa <input> -- sends input to wolframalpha and returns results")
async def wolframalpha(bot: Jenny, room: MatrixRoom, event: HookMessage):
    await bot.room_typing(room.room_id, True, 10000)
    qry = " ".join(event.args).strip()
    if "weather" in qry:
        return await bot.say("reeeeee")
    try:
        res = client.query(qry, units='metric')
    except:
        return await bot.say("Error while querying WolframAlpha")


    print(res)

    if not res["@success"]:
        return await bot.say("No fucking idea.")
    await bot.room_typing(room.room_id, False)

    pods = [x for x in res['pod'] if x['@id'] not in ('CurrentTimePod:TimeZoneData',)][0:2]
    for pod in res['pod']:
        print(pod)

    interp = " ".join([x.text for x in pods if x['@title'] == "Input interpretation"])

    if "convert" in interp or "forecast" in interp or "definition" in interp or "current time" in interp:
        return await bot.say("No fucking idea.")

    if interp:
        interp_sh = interp[0].upper() + interp.replace(" | ", ": ")[1:]
        poddata = []
        for pod in pods[1:2]:
            txd = pod.text
            if "\n" in txd:
                txd = "<br/>&nbsp;&nbsp;" + txd.replace("\n", "<br/>&nbsp;&nbsp;").replace(" | ", ": ")
            poddata.append(txd)
        data = " | ".join([x.text.replace("\n", "<br />") for x in pods[1:2]])
        resp = f"<b>{interp_sh}</b>: {' '.join(poddata)}"
    else:
        if res['@datatypes'] == "Math":
            resp = " = ".join([x.text.replace("\n", " ") for x in pods[0:2]])
        else:
            resp = " | ".join([x.text.replace("\n", " ") for x in pods[0:2]])
    return await bot.message(room.room_id, resp, p_html=True)
