"use strict";

const opentracing = require("opentracing");
const lightstep = require("lightstep-tracer");
const http = require("http");

const satellite_host = "localhost";
const satellite_port = 8360;

const controller_port = 8023;
const controller_host = "localhost";

const millis_per_nano = 1000000;
const prime_work = 982451653;

const noop_tracer = opentracing.initNewTracer(null);
const test_tracer = opentracing.initNewTracer(
  lightstep.tracer({
    access_token: "ignored",
    collector_port: satellite_port,
    collector_host: satellite_host,
    collector_encryption: "none",
    component_name: "javascript/test"
  })
);

console.log("************");

// Note: Keep-Alive does not work properly, reason unknown.  Disable
// it to make progress.
var keepAliveAgent = new http.Agent({
  keepAlive: false
});

function get_control(response) {
  console.log("parsing control response.");

  var body = "";
  response.on("data", function(d) {
    body += d;
    return;
  });
  response.on("end", function() {
    var c = JSON.parse(body);
    console.log(`got control command ${c}`);

    // if we have been told to exit, do it
    if (c.Exit) {
      console.log("got exit command");
      send_done(null, () => {
        process.exit();
      });
    }

    var tracer = c.Trace ? test_tracer : noop_tracer;

    return exec_control(c, tracer);
  });
}

function next_control() {
  console.log("requesting next command.");
  return http.get(
    {
      host: controller_host,
      port: controller_port,
      path: "/control",
      agent: keepAliveAgent
    },
    get_control
  );
}

function send_done(err, callback) {
  console.log("sending done.");
  return http.get(
    {
      host: controller_host,
      port: controller_port,
      path: "/result",
      agent: keepAliveAgent
    },
    () => {
      console.log("get /result callback");
      callback();
    }
  );
}

function exec_control(c, tracer) {
  var begin = process.hrtime();
  var sleep_debt = 0;
  var sleep_at;
  var sleep_nanos = 0;
  var p = prime_work;
  var body_func = function(repeat) {
    if (sleep_debt > 0) {
      var diff = process.hrtime(sleep_at);
      var nanos = diff[0] * 1e9 + diff[1];
      sleep_nanos += nanos;
      sleep_debt -= nanos;
    }
    for (var r = repeat; r > 0; r--) {
      var span = tracer.startSpan("span/test");
      for (var i = 0; i < c.Work; i++) {
        p *= p;
        p %= 2147483647;
      }
      span.finish();
      sleep_debt += c.Sleep;
      if (sleep_debt > c.SleepInterval) {
        sleep_at = process.hrtime();
        return setTimeout(body_func, sleep_debt / millis_per_nano, r - 1);
      }
    }

    // done with work at this point

    var endTime = process.hrtime();
    var elapsed = endTime[0] - begin[0] + (endTime[1] - begin[1]) * 1e-9;

    if (c.Trace && !c.NoFlush) {
      // call next_control when the flush is complete
      return tracer.flush(err => send_done(err, next_control));
    }
    return send_done(null, next_control); // no err
  };
  body_func(c.Repeat);
}

next_control();
