
import React from 'react';
import { getNamedExtensions } from "config/extensions";

// polyfill
if(!Object.assign)
  Object.assign = React.__spread; // eslint-disable-line no-underscore-dangle

require("styles/main.scss")

import config from "config/config";
import modules from 'config/modules';

import Root from 'config/root';

// tie it all together
const Application = require("module-imports?ext=/frontend/application.jsx&path=./beavy_apps/!grep?APP!yaml!../../config.yml").default;

const target = document.getElementById('content');


if (!__DEBUG__){
  if (parent !== window) {
    parent.location.reload();
    throw "iFrame inclusion not allowed!"
  }
}


import configureStore from 'stores';
import { format_jsonapi_result } from 'middleware/api';
let initData = {CURRENT_USER: null}

if (window.PRELOAD && window.PRELOAD.PAYLOAD) initData = format_jsonapi_result(window.PRELOAD.PAYLOAD.data, window.PRELOAD.PAYLOAD.key)

if (window.PRELOAD.CURRENT_USER) initData.CURRENT_USER = window.PRELOAD.CURRENT_USER.data;

const store  = configureStore(initData);


React.render(<Root application={Application}
                   store={store} />, target);
