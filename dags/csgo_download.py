import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from awpy import DemoParser
from playhouse.pool import PooledPostgresqlDatabase
from utils.hltv import (
    download_demo,
    get_match_demo_url,
    get_match_list,
    get_match_more_info,
)
from utils.models import (
    BombEvents,
    Damages,
    Flashes,
    Frames,
    Grenades,
    Kills,
    PlayerFrames,
    Rounds,
    WeaponFires,
    database_proxy,
)
from utils.slack import slack_fail_alert, slack_success_alert

db_info = dict(
    database="csgo",
    user="postgres",
    password="postgres",
    host="postgres",
    port=5432,
    autorollback=True,
)

database_proxy.initialize(
    PooledPostgresqlDatabase(
        **db_info,
        max_connections=5,
        timeout=5,
    )
)


def retrieve_match_list(ds, ti):
    urls = get_match_list(ds)
    ti.xcom_push(key="match_urls", value=urls)
    print(urls)
    print(f"Pong {ds}")


def retrieve_match_more_info(ti):
    urls_match = ti.xcom_pull(key="match_urls")
    urls_info = [get_match_more_info(url) for url in urls_match]
    print(urls_info)
    ti.xcom_push(key="match_info_urls", value=urls_info)


def retrieve_match_demo_url(ti):
    urls_info = ti.xcom_pull(key="match_info_urls")
    print(urls_info)
    urls_demo = [get_match_demo_url(url) for url in urls_info]
    print(urls_demo)
    urls_demo = [url for url in urls_demo if url]
    print(urls_demo)
    ti.xcom_push(key="urls_demo", value=urls_demo)


def download_demos(ds, ti):
    urls_demo = ti.xcom_pull(key="urls_demo")
    print(urls_demo)
    Path(f"/tmp/{ds}").mkdir(parents=True, exist_ok=True)
    for url in urls_demo:
        download_demo(ds, url)


def create_db():
    BombEvents.create_table()
    Damages.create_table()
    Flashes.create_table()
    Frames.create_table()
    Grenades.create_table()
    Kills.create_table()
    PlayerFrames.create_table()
    Rounds.create_table()
    WeaponFires.create_table()


def save_to_db(ds):
    rar_files = list(Path(f"/tmp/{ds}").glob("*.rar"))
    folders = [file.as_posix().replace(".rar", "") for file in rar_files]
    for folder in folders:
        demo_files = list(Path(folder).glob("*.dem"))
        folder_prefix = folder.split("/")[-1]
        print(folder_prefix)
        for demo_file in demo_files:
            print(demo_file)
            demo_parser = DemoParser(
                demofile=demo_file.as_posix(),
                parse_rate=64,
                trade_time=3,
                buy_style="hltv",
            )
            df = demo_parser.parse(return_type="df")
            bomb_events = df["bombEvents"]
            bomb_events["matchID"] = folder_prefix
            bomb_events["ds"] = ds
            BombEvents.insert_many(bomb_events.to_dict("records")).on_conflict(
                "ignore"
            ).execute()

            damages = df["damages"]
            damages["matchID"] = folder_prefix
            damages["ds"] = ds
            damages.zoomLevel.fillna(0, inplace=True)
            Damages.insert_many(damages.to_dict("records")).on_conflict(
                "ignore"
            ).execute()

            flashes = df["flashes"]
            flashes.drop(columns=["matchId"], inplace=True)
            flashes["ds"] = ds
            flashes["matchID"] = folder_prefix
            Flashes.insert_many(flashes.to_dict("records")).on_conflict(
                "ignore"
            ).execute()

            grenades = df["grenades"]
            grenades["matchID"] = folder_prefix
            grenades["ds"] = ds

            Grenades.insert_many(grenades.to_dict("records")).on_conflict(
                "ignore"
            ).execute()

            kills = df["kills"]
            kills["matchID"] = folder_prefix
            kills["ds"] = ds
            Kills.insert_many(kills.to_dict("records")).on_conflict("ignore").execute()

            player_frames = df["playerFrames"]
            player_frames["matchID"] = folder_prefix
            player_frames["ds"] = ds
            PlayerFrames.insert_many(player_frames.to_dict("records")).on_conflict(
                "ignore"
            ).execute()

            rounds = df["rounds"]
            rounds["matchID"] = folder_prefix
            rounds["ds"] = ds
            Rounds.insert_many(rounds.to_dict("records")).on_conflict(
                "ignore"
            ).execute()

            weapon_fires = df["weaponFires"]
            weapon_fires["matchID"] = folder_prefix
            weapon_fires["ds"] = ds
            WeaponFires.insert_many(weapon_fires.to_dict("records")).on_conflict(
                "ignore"
            ).execute()


args = {
    "owner": "airflow",
    "email": ["airflow@example.com"],
    "on_failure_callback": slack_fail_alert,
    "on_success_callback": slack_success_alert,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": datetime.timedelta(seconds=5),
}

dag = DAG(
    dag_id="download_csgo_demo",
    default_args=args,
    schedule_interval="0 1 * * *",
    dagrun_timeout=datetime.timedelta(minutes=120 * 2),
    description="use case of python operator in airflow",
    start_date=datetime.datetime(2022, 1, 1),
    catchup=True,
    max_active_tasks=3,
)


with dag:
    MatchInfoTask = PythonOperator(
        task_id="retrieve_match_list",
        python_callable=retrieve_match_list,
    )
    MatchMoreInfoTask = PythonOperator(
        task_id="retrieve_match_more_info",
        python_callable=retrieve_match_more_info,
    )
    DemoUrlTask = PythonOperator(
        task_id="retrieve_match_demo_url",
        python_callable=retrieve_match_demo_url,
    )
    DownLoadDemos = PythonOperator(
        task_id="download_demos",
        python_callable=download_demos,
    )
    # noqa
    cmd_extract = (
        "cd /tmp/{{ ds }} && find . -name '*.rar' -exec unrar x -ad {} \;" % locals()
    )  # noqa
    ExtractRar = BashOperator(
        task_id="extract_rar",
        bash_command=cmd_extract,
        # bash_command="cd /tmp/ && unrar x -ad *.rar",
    )

    CreateDB = PythonOperator(
        task_id="create_db",
        python_callable=create_db,
    )
    SaveToDb = PythonOperator(
        task_id="save_to_db",
        python_callable=save_to_db,
    )
    cmd_clean_up = (
        "cd /tmp/{{ ds }} && rm -rf /tmp/{{ ds }}/*.rar && find . -type f -name '*.dem' -exec rm {} +"
        % locals()
    )  # noqa
    CleanUp = BashOperator(
        task_id="clean_up",
        bash_command=cmd_clean_up,
    )
    (
        MatchInfoTask
        >> MatchMoreInfoTask
        >> DemoUrlTask
        >> DownLoadDemos
        >> ExtractRar
        >> CreateDB
        >> SaveToDb
        >> CleanUp
    )
