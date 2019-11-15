#!/usr/bin/env python
from dateutil.parser import parse
import datetime
import json
from os.path import isdir, dirname, exists, isfile
from gemeinsprache.utils import normalize_filepath, green, yellow, red, cyan, blue, Pretty as pp
from os import makedirs
import os
from dateutil.relativedelta import relativedelta

app_state = {
    "timestamps": {
        "human": "%A, %B %-d, %Y at %-I:%M%p",
        "human_fixedlength": "%a, %b %d, %Y at %I:%M%p",
        "iso8601": "%Y%m%dT%H%M%SZ",
        "iso8601_dateonly": "%Y%m%d",
        "iso8601_microseconds": "%Y%m%dT%H%M%S.%fZ",
        "generic": "%c"
    }
}


class Kairos:
    def __init__(self):
        config_file = os.path.join(
            os.path.dirname(__file__), ".kairos", "config.json")
        if not config_file.endswith(".json"):
            raise ValueError(f"Not a json file: {config_file}")
        config_file = normalize_filepath(config_file)
        if not isfile(config_file):
            print(yellow(f"No such file: {config_file}"))
            reinitializing = input(
                green("Do you want me to create it? [y/N] "))
            if reinitializing and reinitializing.strip(
            ) and reinitializing.strip()[0].lower() == 'y':
                makedirs(dirname(config_file), exist_ok=True)
                with open(config_file, 'w') as f:
                    f.write(json.dumps(app_state))
                print(green("Initializing a new Kairos configuration file..."))

        self.path_to_config = config_file
        self.is_loaded, self.data, self.err = self.load_appstate()
        self.available_timestamps = [
            ts_name for ts_name, ts_format in self.data['timestamps'].items()
        ]

        self.last_used_format = self.available_timestamps[
            0] if self.is_loaded else None

    def print_available_timestamps(self):
        msg = "Available timestamps are: \n\n"
        left_pad = "     + "
        now = datetime.datetime.now()
        print(green(msg))
        all_ok = True
        for k in self.available_timestamps:
            template = self.data['timestamps'][k]
            ok, rendered, err = self.__render__(template, now)
            if ok:
                timestamp = rendered['timestamp']
                print(
                    f"""{left_pad}{blue(k)}\n          Example: {cyan(timestamp)}\n\n""")
            else:
                print(f"{red(err)}")
                pp(rendered).print()
                all_ok = False
                continue
        return all_ok

    def __render__(self, template, dt=None):
        errs = []
        if dt is None:
            dt = datetime.datetime.now()
        try:
            timestamp = dt.strftime(template)
        except Exception as err:
            timestamp = ""
            errs.append(err)
        try:
            deserialized = parse(timestamp)
        except Exception as err:
            deserialized = None
            errs.append(err)
        is_deserializable = deserialized and deserialized is not None
        ok = is_deserializable and not errs
        return ok, locals(), errs

    def create_timestamp(self, dt, name=None):
        if name is None:
            name = self.last_used_timestamp
        elif name in self.available_timestamps:
            self.last_used_timestamp = name
        if name not in self.available_timestamps:
            print(
                f"""{red("I don't have a timestamp called")} {yellow(name)}."""
            )
            self.print_available_timestamps()
            return None
        ok, template, err = self.load_template(name)
        if not ok:
            print(f"""Template Error: {red(err)}""")
            pp(template).print()
            self.print_available_timestamps()
            return None
        ok, rendered, err = self.__render__(template=template, dt=dt)
        if not ok:
            print(f"""Rendering Error: {red(err)}""")
            pp(rendered).print()
            self.print_available_timestamps()
            return None
        if rendered['ok']:
            return rendered['timestamp']
        else:
            print(f"""{red("Error creating a timestamp from args: ")}""")
            pp(rendered).print()
            self.print_available_timestamps()
            return None

    def load_template(self, name):
        err = None
        try:
            template = self.data['timestamps'][name]
        except Exception as err:
            template = ""
        ok = err is None
        return ok, template, err

    def load_appstate(self):
        err = None
        with open(self.path_to_config, 'r') as f:
            try:
                data = json.loads(f.read())
            except Exception as err:
                data = {}
        ok = err is None
        return ok, data, err

def create_timestamp(dt: datetime.datetime, timestamp_format='human_fixedlength') -> str:
    k = Kairos()
    ts = k.create_timestamp(dt, timestamp_format)
    return ts

def parse_timestamp(ts: str, timestamp_format=None) -> str:
    if timestamp_format:
        k = Kairos()
        if timestamp_format in k.available_timestamps:
            template = k.load_template(timestamp_format)
            parsed = ts.strptime(template)
        else:
            parsed = ts.strptime(timestamp_format)
    else:
        parsed = parse(ts)
    return parsed
if __name__ == '__main__':
    k = Kairos()
    print(k.available_timestamps)
    ok = k.print_available_timestamps()
    msg = green("OK") if ok else red("FAIL")
    now = datetime.datetime.now()
    ts = create_timestamp(now)
    print(f"Converted {yellow(now)} to {yellow(ts)}")
    print(msg)
