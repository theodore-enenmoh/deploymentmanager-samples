# Copyright 2015 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Creates a backend-service that replicates autoscaled_group across X zones."""

import copy

import autoscaled_group
import common
import default

# Properties in use by this component
HEALTH_PATH = default.HEALTH_PATH
PORT = default.PORT
REPLICAS = default.REPLICAS
SERVICE = default.SERVICE

# Generated in the REPLICAS properties
GENERATED_PROP = default.GENERATED_PROP
GEN_NAME = 'generatedName'


def GenerateBackendService(context):
  """Generates one backendService resource."""
  prop = context.properties
  port = prop[default.PORT]
  health_path = prop[default.HEALTH_PATH]
  default_srv = prop[default.SERVICE]
  outputs = prop.setdefault(GENERATED_PROP, dict())
  be_name = common.AutoName(context.env['name'], default.BACKEND_SERVICE)
  hc_name = common.AutoName(context.env['name'], default.HEALTHCHECK)

  # pyformat: disable
  resource = [
      {
          'name': hc_name,
          'type': default.HEALTHCHECK,
          'properties': {
              'port': port,
              'requestPath': health_path,
          }
      }, {
          'name': be_name,
          'type': default.BACKEND_SERVICE,
          'properties': {
              'port': port,
              'portName': default_srv,
              'backends': GenerateBackends(context),
              'healthChecks': [common.Ref(hc_name)],
              'generatedProperties': outputs
          }
      }
  ]
  # pyformat: enable
  return resource


def GenerateBackends(context):
  """Generates dictionary of IGMs connected to a backeend service."""
  name = context.env['name']
  prop = context.properties
  replicas = prop[REPLICAS]
  backends = []
  for zone_dict in replicas:
    short_abbrv = common.ShortenZoneName(zone_dict[default.ZONE])
    ig_name = common.AutoName(name, default.IGM, short_abbrv)
    zone_dict[GEN_NAME] = ig_name
    backend = {'name': ig_name, 'group': common.RefGroup(ig_name)}
    backends.append(backend)
  prop[GENERATED_PROP][REPLICAS] = copy.deepcopy(replicas)
  return backends


def GenerateResourceList(context):
  """Returns list of resources generated by this module."""
  resources = autoscaled_group.GenerateNAutoscaledGroup(context)
  resources += GenerateBackendService(context)
  return resources


@common.FormatErrorsDec
def GenerateConfig(context):
  """Generates YAML resource configuration."""
  return common.MakeResource(GenerateResourceList(context))
