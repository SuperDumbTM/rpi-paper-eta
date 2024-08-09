from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

import pytz
from .enums import Locale
from .models import Eta
from .eta_processor import _8601str


def _logo(name: str) -> BytesIO:
    with open(Path(__file__).parent.joinpath("images", "bw_neg", f"{name}.bmp"), 'rb') as b:
        return BytesIO(b.read())


STZ = pytz.timezone("Etc/GMT-8")

TESTS_TC = [
    Eta(no="1",
        origin="尖沙嘴碼頭",
        destination="竹園邨",
        stop_name="康強苑",
        locale=Locale.TC,
        logo=_logo("kmb"),
        etas=[
            Eta.Time(
                destination="竹園邨",
                is_arriving=False,
                is_scheduled=False,
                eta=_8601str(datetime.now(STZ) + timedelta(minutes=6)),
                eta_minute=(datetime.now(STZ) + timedelta(minutes=7)).minute,
                remark="行車受阻@喇沙小學"
            ),
            Eta.Time(
                destination="竹園邨",
                is_arriving=False,
                is_scheduled=True,
                eta=_8601str(datetime.now(STZ) + timedelta(minutes=15)),
                eta_minute=(datetime.now(STZ) + timedelta(minutes=15)).minute,
            ),
            Eta.Time(
                destination="竹園邨",
                is_arriving=False,
                is_scheduled=True,
                eta=_8601str(datetime.now(STZ) + timedelta(minutes=23)),
                eta_minute=(datetime.now(STZ) + timedelta(minutes=23)).minute,
            )
        ],
        timestamp=datetime.now().replace(tzinfo=STZ)
        ),
    Eta(no="610",
        origin="元朗",
        destination="屯門碼頭",
        stop_name="豐年路",
        locale=Locale.TC,
        logo=_logo("mtr_lrt"),
        etas=[
            Eta.Time(
                destination="屯門碼頭",
                is_arriving=False,
                is_scheduled=False,
                eta=_8601str(datetime.now(STZ) + timedelta(minutes=2)),
                eta_minute=(datetime.now(STZ) + timedelta(minutes=2)).minute,
            ),
            Eta.Time(
                destination="屯門碼頭",
                is_arriving=False,
                is_scheduled=True,
                eta=_8601str(datetime.now(STZ) + timedelta(minutes=12)),
                eta_minute=(datetime.now(STZ) + timedelta(minutes=12)).minute,
            ),
        ],
        timestamp=datetime.now().replace(tzinfo=STZ)
        ),
    Eta(no="東鐵線",
        origin="金鐘",
        destination="羅湖",
        stop_name="旺角東",
        locale=Locale.TC,
        logo=_logo("mtr_train"),
        etas=[
            Eta.Time(
                destination="羅湖",
                is_arriving=True,
                is_scheduled=False,
                eta=_8601str(datetime.now(STZ) + timedelta(minutes=1)),
                eta_minute=(datetime.now(STZ) + timedelta(minutes=1)).minute,
                extras={"platform": 1},
            ),
            Eta.Time(
                destination="羅湖",
                is_arriving=False,
                is_scheduled=False,
                eta=_8601str(datetime.now(STZ) + timedelta(minutes=6)),
                eta_minute=(datetime.now(STZ) + timedelta(minutes=6)).minute,
                extras={"platform": 1, "route_variant": "RAC"},
            ),
            Eta.Time(
                destination="落馬洲",
                is_arriving=False,
                is_scheduled=True,
                eta=_8601str(datetime.now(STZ) + timedelta(minutes=13)),
                eta_minute=(datetime.now(STZ) + timedelta(minutes=13)).minute,
                extras={"platform": 1},
            ),
        ],
        timestamp=datetime.now().replace(tzinfo=STZ)
        ),
    Eta(no="948",
        origin="天后站",
        destination="長安邨",
        stop_name="堅拿道東, 軒尼詩道",
        locale=Locale.TC,
        logo=_logo("ctb"),
        etas=[
            Eta.Time(
                destination="長安邨",
                is_arriving=False,
                is_scheduled=False,
                eta=_8601str(datetime.now(STZ) + timedelta(minutes=12)),
                eta_minute=(datetime.now(STZ) + timedelta(minutes=12)).minute,
            ),
            Eta.Time(
                destination="長安邨",
                is_arriving=False,
                is_scheduled=True,
                eta=None,
                eta_minute=None,
                remark="九巴班次"
            ),
            Eta.Time(
                destination="長安邨",
                is_arriving=False,
                is_scheduled=True,
                eta=_8601str(datetime.now(STZ) + timedelta(minutes=52)),
                eta_minute=(datetime.now(STZ) + timedelta(minutes=52)).minute,
            ),
        ],
        timestamp=datetime.now().replace(tzinfo=STZ)
        ),
    Eta(no="N214",
        origin="油塘",
        destination="美孚",
        stop_name="安泰(南)(恆泰樓)",
        locale=Locale.TC,
        logo=_logo("kmb"),
        etas=Eta.Error(message="服務時間已過"),
        timestamp=datetime.now().replace(tzinfo=STZ)
        ),
    Eta(no="4",
        origin="塘福",
        destination="梅窩碼頭",
        stop_name="長沙下村",
        locale=Locale.TC,
        logo=_logo("nlb"),
        etas=[
            Eta.Time(
                destination="梅窩碼頭",
                is_arriving=False,
                is_scheduled=True,
                eta=_8601str(datetime.now(STZ) + timedelta(minutes=18)),
                eta_minute=(datetime.now(STZ) + timedelta(minutes=18)).minute,
            ),
            Eta.Time(
                destination="梅窩碼頭",
                is_arriving=False,
                is_scheduled=True,
                eta=_8601str(datetime.now(STZ) + timedelta(minutes=69)),
                eta_minute=(datetime.now(STZ) + timedelta(minutes=69)).minute,
            ),
        ],
        timestamp=datetime.now().replace(tzinfo=STZ)
        ),
]
