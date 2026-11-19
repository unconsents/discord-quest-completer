import asyncio,base64,hashlib,importlib,importlib.metadata as _md,json,os,random,re,shutil,subprocess,sys,time,zlib
from datetime import datetime, timezone

def _has(name):
    for n in {name,name.replace(".","-"),name.replace(".","_"),name.replace("-","_")}:
        try:
            _md.version(n);return True
        except _md.PackageNotFoundError:
            continue
    return False

def _pip(*args):
    return subprocess.run([sys.executable,"-m","pip",*args,"--disable-pip-version-check","-q"]).returncode==0

def _bootstrap():
    required=["aiohttp","colour","discord.py-self"]
    conflict=_has("discord.py")
    missing=[p for p in required if not _has(p)]
    if not conflict and not missing:return
    if conflict:
        print("discord.py is installed and conflicts with discord.py-self (both provide the 'discord' module), so it is being removed.")
        if not _pip("uninstall","-y","discord.py"):
            print("Failed to uninstall discord.py, please run: pip uninstall discord.py");sys.exit(1)
        if not _pip("install","--force-reinstall","--no-deps","discord.py-self"):
            print("Failed to install discord.py-self, please run: pip install discord.py-self");sys.exit(1)
    print("Installing required packages: "+", ".join(missing if missing else ["discord.py-self"]))
    if not _pip("install",*required):
        print("Package installation failed, please run: pip install "+" ".join(required));sys.exit(1)
    importlib.invalidate_caches()
    print("Packages ready.\n")

_bootstrap()

import aiohttp,discord
from colour import Color

def _enable_vt():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if os.name=="nt":
        try:
            import ctypes
            k=ctypes.windll.kernel32;h=k.GetStdHandle(-11);m=ctypes.c_ulong()
            k.GetConsoleMode(h,ctypes.byref(m));k.SetConsoleMode(h,m.value|4)
        except Exception:
            pass

_enable_vt()

clr_ok    = "\033[38;2;214;170;255m"
clr_warn  = "\033[38;2;255;190;90m"
clr_err   = "\033[38;2;255;100;120m"
clr_dim   = "\033[38;2;128;112;165m"
clr_reset = "\033[0m"

grad_stops = [(112,62,214),(147,80,240),(182,110,250),(214,150,255),(240,205,255)]
grad_acct  = ["\033[38;2;196;148;255m","\033[38;2;132;144;255m","\033[38;2;232;121;249m","\033[38;2;168;110;240m","\033[38;2;255;150;220m","\033[38;2;120;190;255m"]

NAME_PAD   = 28
TAG_PAD    = 12
BAR_WIDTH  = 20
NUM_PAD    = 5
STATUS_PAD = 10

_credits = zlib.decompress(base64.b64decode("eNrLTUxJVUiqVMjMS8tJzM1NTMrMySzJTC1WyM9TSMksTs4vSgEA7IkNUg==")).decode()
_key     = hashlib.sha256(_credits.encode()).digest()

def _unseal(data):
    return bytes(b^_key[i%len(_key)] for i,b in enumerate(base64.b64decode(data))).decode()

ansi_re = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
tty     = sys.stdout.isatty()
live_on = False
drawn   = 0
pending = False

def write(s):
    sys.stdout.write(s);sys.stdout.flush()

def ansi(rgb):
    return "\033[38;2;%d;%d;%dm"%rgb

def build_ramp(stops,steps=64):
    ramp=[]
    for a,b in zip(stops,stops[1:]):
        ca=Color(rgb=tuple(v/255 for v in a))
        cb=Color(rgb=tuple(v/255 for v in b))
        seg=[tuple(min(255,max(0,int(round(c*255)))) for c in col.rgb) for col in ca.range_to(cb,steps)]
        ramp.extend(seg if not ramp else seg[1:])
    return ramp

ramp = build_ramp(grad_stops)

def ramp_at(t):
    t=max(0.,min(t,1.))
    return ramp[int(t*(len(ramp)-1)+0.5)]

def grad_text(text,width=None):
    n=max((width or len(text))-1,1)
    return "".join(ansi(ramp_at(i/n))+ch if ch!=" " else ch for i,ch in enumerate(text))+clr_reset

icon_info = ansi(ramp_at(0.5))
icon_ok   = ansi(ramp_at(1.0))
icon_warn = clr_warn
icon_err  = clr_err

_banner_lines = [
    ".▄▄▄  ▄• ▄▌▄▄▄ ..▄▄ · ▄▄▄▄▄",
    "▐▀•▀█ █▪██▌▀▄.▀·▐█ ▀. •██  ",
    "█▌·.█▌█▌▐█▌▐▀▀▪▄▄▀▀▀█▄ ▐█.▪",
    "▐█▪▄█·▐█▄█▌▐█▄▄▌▐█▄▪▐█ ▐█▌·",
    "·▀▀█.  ▀▀▀  ▀▀▀  ▀▀▀▀  ▀▀▀ ",
]
_banner_width = max(len(l) for l in _banner_lines)
_subtitle     = "Discord Quest Completer"

def centered(text,width,cols):
    return " "*max((cols-width)//2,0)+text

def build_banner():
    cols=shutil.get_terminal_size((120,30)).columns
    art=[centered(grad_text(l,_banner_width),_banner_width,cols) for l in _banner_lines]
    sub=centered(clr_dim+_subtitle+clr_reset,len(_subtitle),cols)
    cred=centered(grad_text(_credits),len(_credits),cols)
    return "\n"+"\n".join(art)+"\n"+sub+"\n"+cred+"\n"

def fmt_name(name):
    return (name[:NAME_PAD-3]+"...") if len(name)>NAME_PAD else name.ljust(NAME_PAD)

def fmt_bar(pct,width=BAR_WIDTH):
    filled=round(pct*width)
    bar="".join(ansi(ramp_at(i/max(width-1,1)))+"#" for i in range(filled))
    return bar+clr_dim+"-"*(width-filled)+clr_reset

def ts(at=None):
    return clr_dim+(at or datetime.now()).strftime("%H:%M:%S")+clr_reset

def pfx(tag,col):
    if not tag:return " "*(TAG_PAD+2)
    return f"{col}[{tag[:TAG_PAD].ljust(TAG_PAD)}]{clr_reset}"

rows       = {}
acct_order = []

status_style = {"done":clr_ok,"failed":clr_err}

def crop(line,cols):
    res=[];vis=0;i=0
    while i<len(line):
        m=ansi_re.match(line,i)
        if m:
            res.append(m.group());i=m.end();continue
        if vis<cols:
            res.append(line[i]);vis+=1
        i+=1
    return "".join(res)+clr_reset

def render_row(r):
    cur,tgt=r["cur"],r["tgt"]
    pct=min(cur/tgt,1.) if tgt else 1.
    status=r["status"]
    if status is None:
        rem=max(0,tgt-cur)
        cell=clr_dim+f"{int(rem//60):>3}:{int(rem%60):02d} left".ljust(STATUS_PAD)+clr_reset
    else:
        cell=status_style.get(status,clr_dim)+status.ljust(STATUS_PAD)+clr_reset
    nums=f"{int(cur):>{NUM_PAD}}/{str(int(tgt))+'s':<{NUM_PAD+1}}"
    return f"{ts(r['at'])}  {pfx(r['tag'],r['col'])}  {r['icon_col']}{r['icon']}{clr_reset}  {fmt_name(r['name'])}  {fmt_bar(pct)}  {clr_dim}{int(pct*100):>3}%  {nums}{clr_reset}  {cell}"

def sorted_rows():
    order={t:i for i,t in enumerate(acct_order)}
    return sorted(list(rows.values()),key=lambda r:order.get(r["tag"],0))

def clear_region():
    global drawn
    if drawn:write(f"\033[{drawn}A\r\033[J")
    drawn=0

def draw_region():
    global drawn
    cols=max(shutil.get_terminal_size((120,30)).columns-1,20)
    lines=[crop(render_row(r),cols) for r in sorted_rows()]
    if lines:write("".join(l+"\n" for l in lines))
    drawn=len(lines)

def out(line=""):
    if live_on and tty:
        clear_region();write(line+clr_reset+"\n");draw_region()
    else:
        write(line+clr_reset+"\n")

def refresh():
    global pending
    pending=False
    if live_on and tty:
        clear_region();draw_region()

def notify(r):
    global pending
    if not tty:
        out(render_row(r));return
    if pending:return
    pending=True
    asyncio.get_running_loop().call_later(0.1,refresh)

def live_start():
    global live_on
    live_on=True
    if tty:
        write("\033[?25l");draw_region()

def live_stop():
    global live_on
    if tty and live_on:
        clear_region();draw_region();write("\033[?25h")
    live_on=False

def emit(icon,icon_col,body,tag="",col=""):
    out(f"{ts()}  {pfx(tag,col)}  {icon_col}{icon}{clr_reset}  {body}")

def log_info(msg,tag="",col=""):
    emit(">",icon_info,msg,tag,col)

def log_ok(msg,tag="",col=""):
    emit("+",icon_ok,msg,tag,col)

def log_warn(msg,tag="",col=""):
    emit("!",icon_warn,msg,tag,col)

def log_err(msg,tag="",col=""):
    emit("x",icon_err,msg,tag,col)

def set_row(name,cur,tgt,icon,icon_col,tag,col):
    r=rows.get((tag,name))
    if r is None:
        r=rows[(tag,name)]={"status":None,"cur":None,"tgt":None}
        if tag not in acct_order:acct_order.append(tag)
    changed=r["cur"]!=cur or r["tgt"]!=tgt
    r.update(name=name,cur=cur,tgt=tgt,icon=icon,icon_col=icon_col,tag=tag,col=col)
    if changed:
        r["at"]=datetime.now();notify(r)

def mark(name,status,tag="",col=""):
    r=rows.get((tag,name))
    if not r or r["status"]==status:return
    r["status"]=status;r["at"]=datetime.now()
    if status=="done":r["cur"]=r["tgt"]
    notify(r)

def log_video(name,cur,tgt,tag="",col=""):
    set_row(name,cur,tgt,"@",ansi(ramp_at(0.3)),tag,col)

def log_beat(name,cur,tgt,task,tag="",col=""):
    set_row(name,cur,tgt,">",ansi(ramp_at(1.0)),tag,col)

base_dir    = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_dir,"config.json")
tokens_path = os.path.join(base_dir,"tokens.txt")

def load_config():
    if not os.path.exists(config_path):
        out(f"{clr_err}config.json not found{clr_reset}");sys.exit(1)
    return json.load(open(config_path,encoding="utf-8"))

def load_tokens():
    if not os.path.exists(tokens_path):
        out(f"{clr_err}tokens.txt not found{clr_reset}");sys.exit(1)
    toks=[l.strip() for l in open(tokens_path,encoding="utf-8") if l.strip()]
    if not toks:out(f"{clr_err}tokens.txt is empty{clr_reset}");sys.exit(1)
    return toks

cfg           = load_config()
all_tokens    = load_tokens()
timezone_str  = cfg.get("timezone","America/New_York")
locale        = cfg.get("locale","en-US")

desktop_ua      = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9268 Chrome/152.0.7977.169 Electron/44.10.2 Safari/537.36"
api_base        = _unseal("VbXY5+Z+nQsYWMAvos9pzHl+zQxTvRpB5ug=")
auth_key        = _unseal("fLTY//o2214dRdojow==")
task_priority   = ["WATCH_VIDEO","WATCH_VIDEO_ON_MOBILE","PLAY_ON_DESKTOP","STREAM_ON_DESKTOP","PLAY_ACTIVITY"]
heartbeat_tasks = {"PLAY_ON_DESKTOP","STREAM_ON_DESKTOP","PLAY_ACTIVITY"}
video_tasks     = {"WATCH_VIDEO","WATCH_VIDEO_ON_MOBILE"}
max_failures    = 5

super_props = base64.b64encode(json.dumps({
    "os": "Windows",
    "browser": "Discord Client",
    "release_channel": "stable",
    "client_build_number": 673919,
    "os_version": "10.0.22631",
    "os_arch": "x64",
    "app_arch": "x64",
    "system_locale": locale,
    "browser_user_agent": desktop_ua,
    "browser_version": "152.0.7977.169",
    "client_event_source": None,
}, separators=(",", ":")).encode()).decode()

def req_headers(token):
    return {
        auth_key:token,"User-Agent":desktop_ua,
        "Content-Type":"application/json","X-Super-Properties":super_props,
        "X-Discord-Locale":locale,"X-Discord-Timezone":timezone_str,
    }

async def http_request(sess,method,path,token,body=None):
    attempt=0
    while True:
        async with sess.request(method,f"{api_base}{path}",headers=req_headers(token),json=body) as r:
            if r.status==204:return{}
            try:data=await r.json(content_type=None)
            except Exception:data={}
            if r.status==429:
                await asyncio.sleep(float((data or {}).get("retry_after",1))+0.05);continue
            if r.status>=500:
                attempt+=1
                if attempt>5:raise Exception(f"{r.status}:{data}")
                await asyncio.sleep(min(2**attempt,30));continue
            if r.status not in(200,202,204):raise Exception(f"{r.status}:{data}")
            return data if data is not None else {}

async def http_get(sess,path,token):
    return await http_request(sess,"GET",path,token)

async def http_post(sess,path,body,token):
    return await http_request(sess,"POST",path,token,body)

def parse_ts(s):
    return 0.0 if not s else datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000+00:00")

def get_tasks(quest):
    tc=quest["config"].get("task_config_v2")
    if not tc:return[]
    if tc.get("type")==2:return[]
    tasks=tc.get("tasks") or {}
    if tc.get("join_operator")=="and":
        picked=[(n,d) for n,d in tasks.items() if d is not None]
        if not picked or any(n not in video_tasks and n not in heartbeat_tasks for n,_ in picked):return[]
        return picked
    for name in task_priority:
        if tasks.get(name) is not None:return[(name,tasks[name])]
    return[]

def user_status(quest):
    return quest.get("user_status") or {}

def get_progress(us,task):
    bt=(us.get("progress")or{}).get(task,{})
    if "value" in bt:return float(bt["value"])
    return 0.0

def task_done(quest,task,task_data):
    bt=(user_status(quest).get("progress")or{}).get(task,{})
    if bt.get("completed_at") is not None:return True
    target=float(task_data.get("target",0))
    return target>0 and float(bt.get("value",0))>=target

def split_quests(quest_list):
    now=time.time();enrolled=[];unenrolled=[]
    for q in quest_list:
        us=user_status(q);exp=q["config"].get("expires_at","")
        if exp and parse_ts(exp)<=now:continue
        if bool(us.get("claimed_at")):continue
        if bool(us.get("completed_at")):continue
        if not get_tasks(q):continue
        if bool(us.get("enrolled_at")):enrolled.append(q)
        else:unenrolled.append(q)
    return enrolled,unenrolled

async def run_video(sess,quest,task,task_data,token,tag,col):
    qid=quest["id"];name=quest["config"]["messages"]["quest_name"]
    us=user_status(quest);target=float(task_data.get("target",0))
    progress=get_progress(us,task)
    enrolled_ts=parse_ts(us.get("enrolled_at",""))
    if enrolled_ts==0.0:enrolled_ts=time.time()
    try:
        await http_post(sess,f"/quests/{qid}/video-progress",{"timestamp":0},token)
        await asyncio.sleep(1)
    except Exception:pass
    log_video(name,progress,target,tag,col);done=False;fails=0
    while not done and progress<target:
        if(time.time()-enrolled_ts)+10-progress>=7:
            nxt=min(target,progress+7+random.random())
            try:
                resp=await http_post(sess,f"/quests/{qid}/video-progress",{"timestamp":int(nxt)},token)
                fails=0
                progress=nxt;log_video(name,progress,target,tag,col)
                tp=(resp.get("progress")or{}).get(task,{})
                if tp.get("completed_at") is not None or progress>=target:done=True
            except Exception as e:
                fails+=1;log_err(f"{name}:{e}",tag,col)
                if fails>=max_failures:raise
        if not done:await asyncio.sleep(1)
    if not done:
        try:await http_post(sess,f"/quests/{qid}/video-progress",{"timestamp":int(target)},token)
        except Exception as e:log_err(f"{name}:{e}",tag,col)
    mark(name,"done",tag,col)

async def run_heartbeat(sess,quest,task,task_data,token,tag,col):
    qid=quest["id"];name=quest["config"]["messages"]["quest_name"]
    us=user_status(quest);target=float(task_data.get("target",0))
    progress=get_progress(us,task);skey=f"call:{qid}:1"
    app_id=(quest["config"].get("application")or{}).get("id")
    body={"stream_key":skey,"terminal":False}
    if app_id:body["application_id"]=app_id
    log_beat(name,progress,target,task,tag,col);fails=0
    while True:
        try:
            resp=await http_post(sess,f"/quests/{qid}/heartbeat",body,token)
            fails=0
            task_prog=(resp.get("progress")or{}).get(task,{})
            progress=float(task_prog.get("value",progress))
            log_beat(name,progress,target,task,tag,col)
            if progress>=target or task_prog.get("completed_at") is not None:
                await http_post(sess,f"/quests/{qid}/heartbeat",{**body,"terminal":True},token);break
        except Exception as e:
            fails+=1;log_err(f"{name}:{e}",tag,col)
            if fails>=max_failures:raise
        await asyncio.sleep(30)
    mark(name,"done",tag,col)

async def run_account(token,tag,col):
    async with aiohttp.ClientSession() as sess:
        log_info("Fetching quests...",tag,col)
        try:
            resp=await http_get(sess,"/quests/@me",token)
        except Exception as e:
            log_err(f"Failed to fetch quests:{e}",tag,col);return
        quests=resp.get("quests",[])
        blocked_until=resp.get("quest_enrollment_blocked_until")
        if blocked_until:
            log_warn(f"Enrollment blocked until {blocked_until}",tag,col)
        enrolled,unenrolled=split_quests(quests)
        if unenrolled and not blocked_until:
            log_info(f"Auto-enrolling {len(unenrolled)} quest(s)...",tag,col)
            for q in unenrolled:
                qname=q["config"]["messages"]["quest_name"]
                try:
                    us=await http_post(sess,f"/quests/{q['id']}/enroll",{"location":11},token)
                    q["user_status"]=us if us else {"enrolled_at":now_iso(),"completed_at":None,"claimed_at":None,"progress":{}}
                    enrolled.append(q)
                    log_ok(f"Enrolled: {qname}",tag,col)
                except Exception as e:log_err(f"Could not enroll {qname}: {e}",tag,col)
            await asyncio.sleep(1)
        if not enrolled:log_warn("No eligible quests found",tag,col);return
        log_info(f"Running {clr_ok}{len(enrolled)}{clr_reset} quest(s) concurrently",tag,col)
        async def handle(quest):
            tasks=get_tasks(quest);name=quest["config"]["messages"]["quest_name"]
            if not tasks:
                log_warn(f"No automatable task for: {name}",tag,col);return
            try:
                for task,task_data in tasks:
                    if task_done(quest,task,task_data):continue
                    if task in video_tasks:
                        await run_video(sess,quest,task,task_data,token,tag,col)
                    else:
                        await run_heartbeat(sess,quest,task,task_data,token,tag,col)
            except Exception as e:
                log_err(f"{name}:{e}",tag,col)
                mark(name,"failed",tag,col)
        await asyncio.gather(*[handle(q) for q in enrolled])
        log_ok("All quests finished, claim your rewards in the Discord client",tag,col)

async def main():
    out(build_banner());account_map={}
    async def login(token,idx):
        col=grad_acct[idx%len(grad_acct)];client=discord.Client();ev=asyncio.Event()
        @client.event
        async def on_ready():
            tag=str(client.user).split("#")[0][:12]
            log_ok(f"Logged in as {col}{client.user}{clr_reset}  {clr_dim}({client.user.id}){clr_reset}",tag,col)
            account_map[token]=(tag,col,client);ev.set()
        async def try_start():
            try:
                await client.start(token)
            except discord.LoginFailure:
                preview=token[:16]+"..."
                log_err(f"Invalid token ({preview}), removing from tokens.txt")
                lines=[l.strip() for l in open(tokens_path,encoding="utf-8") if l.strip() and l.strip()!=token]
                open(tokens_path,"w",encoding="utf-8").write("\n".join(lines)+("\n" if lines else ""))
                ev.set()
            except Exception as e:
                log_err(f"Login error: {e}");ev.set()
        asyncio.create_task(try_start());await ev.wait()
    await asyncio.gather(*[login(t,i) for i,t in enumerate(all_tokens)])
    out()
    live_start()
    try:
        await asyncio.gather(*[run_account(tok,tag,col) for tok,(tag,col,_) in account_map.items()])
    finally:
        live_stop()
    for _,_,client in account_map.values():await client.close()

asyncio.run(main())
