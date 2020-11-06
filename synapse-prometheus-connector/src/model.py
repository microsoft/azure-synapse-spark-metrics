import json
import time
import typing
from typing import Any, List, Optional

import attr
import cattr
import timestring
import yaml
from attr import attrib, attrs


@attrs(auto_attribs=True)
class SparkApplication(object):
    state: Optional[str]
    name: Optional[str]
    submitter: Optional[str]
    compute: Optional[str]
    sparkPoolName: Optional[str]
    sparkApplicationId: Optional[str]
    livyId: Optional[str]
    timing: List[Any]
    jobType: Optional[str]
    submitTime: Optional[str]
    endTime: Optional[str]
    queuedDuration: Optional[str]
    runningDuration: Optional[str]
    totalDuration: Optional[str]
    _queued_duration_seconds: Optional[int] = attrib(default=None)
    _running_duration_seconds: Optional[int] = attrib(default=None)
    _total_duration_seconds: Optional[int] = attrib(default=None)

    @property
    def spark_pool_name(self):
        return self.sparkPoolName
    
    @property
    def spark_application_id(self):
        return self.sparkApplicationId
    
    @property
    def livy_id(self):
        return self.livyId
    
    @property
    def job_type(self):
        return self.jobType
    
    @property
    def submit_time(self):
        return self.submitTime
    
    @property
    def submit_time_seconds(self):
        return int(time.mktime(timestring.Date(self.submitTime).date.timetuple()))
    
    @property
    def end_time(self):
        return self.endTime
    
    @property
    def end_time_seconds(self):
        if self.end_time:
            return int(time.mktime(timestring.Date(self.endTime).date.timetuple()))
        return 0

    @property
    def queued_duration_seconds(self):
        if self._queued_duration_seconds is None:
            self._queued_duration_seconds = self._convert_to_seconds(self.queuedDuration)
        return self._queued_duration_seconds

    @property
    def running_duration_seconds(self):
        if self._running_duration_seconds is None:
            self._running_duration_seconds = self._convert_to_seconds(self.runningDuration)
        return self._running_duration_seconds

    @property
    def total_duration_seconds(self):
        if self._total_duration_seconds is None:
            self._total_duration_seconds = self._convert_to_seconds(self.totalDuration)
        return self._total_duration_seconds

    def _convert_to_seconds(self, s):
        return sum(map(lambda x: len(timestring.Range(x)), s.split(' ')))


def spark_application_from_dict(d):
    obj = cattr.structure(d, SparkApplication)
    return obj


@attrs(auto_attribs=True)
class PrometheusStaticConfig(object):
    targets: typing.List[str] = attrib()
    labels: dict = attrib()


@attrs(auto_attribs=True)
class PrometheusFileSdConfig(object):
    refresh_interval: str = attrib(default='10s')
    files: typing.List[str] = attrib(factory=list)


@attrs(auto_attribs=True)
class SynapseScrapeConfig(object):
    job_name: str = attrib()
    bearer_token: str = attrib(default=None)
    static_configs: typing.List[PrometheusStaticConfig] = attrib(default=None)
    file_sd_configs: typing.List[PrometheusFileSdConfig] = attrib(default=None)


@attrs(auto_attribs=True)
class SynapseScrapeConfigs(object):
    configs: typing.List[SynapseScrapeConfig] = attrib(factory=list)

    def to_yaml(self):
        return to_yaml(self.configs)
    
    def to_dict(self):
        return to_dict(self.configs)


def to_yaml(obj):
    return yaml.safe_dump(cattr.unstructure(obj))

def to_dict(obj):
    return cattr.unstructure(obj)

def to_json(obj):
    return json.dumps(to_dict(obj), indent=2)
