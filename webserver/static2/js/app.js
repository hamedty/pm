var app = angular.module('app', ['ngWebSocket']);
// ------------- websocket wrapper -------------
app.factory('ws', function($websocket) {
  // Open a WebSocket connection
  var dataStream = $websocket("ws://" + location.host + "/ws", null, {
    reconnectIfNotNormalClose: true
  });

  var methods = {
    onMessage: function(cb) {
      dataStream.onMessage(cb)
    },
    onClose: function(cb) {
      dataStream.onClose(cb)
    },
    get: function(data) {
      dataStream.send(JSON.stringify(data));
    }
  };

  return methods;
})



// ------------- main controller -------------
app.controller('app_controller', function($scope, ws) {

  // ------------- initialization -------------
  const dafault_local_data = {
    'no_connection': true,
    'page_selected': ['home'],
  };

  const consts = {
    'main_frame_urls': {
      'home': '/static2/html/home.html',
    },
  }

  initialize = function() {
    $scope.local_data = JSON.parse(JSON.stringify(dafault_local_data));
    $scope.remote_data = {};
    $scope.consts = consts;
    $scope.fn_change_page(['home'])
  }

  ws.onMessage(function(message) {
    message = JSON.parse(message.data).v2;
    if (message) {
      $scope.local_data.no_connection = false;
      $scope.remote_data = message;
      $scope.remote_data.time_stamp = moment();
    }
  });

  ws.onClose(function() {
    console.log('connection closed');
    initialize();
  });

  // ------------- functionalities -------------
  $scope.fn_change_page = function(page_selected) {
    // page_selected = ['settings']
      $scope.local_data.page_selected = page_selected;
      $scope.local_data.main_frame_url = $scope.consts.main_frame_urls[$scope.local_data.page_selected[0]]
  }

  $scope.fn_run_script = function(script_name) {
    console.log('run script', script_name);
    command = {
      'type': 'run_script',
      'script_name': script_name,
    }
    ws.get(command);
  }

  $scope.fn_stop = function() {
    console.log('stop button');
    command = {
      'type': 'system_stop',
    }
    ws.get(command);
  }

  $scope.fn_pause = function(paused) {
    console.log('pause button');
    command = {
      'type': paused ? 'system_play': 'system_pause',
    }
    ws.get(command);
  }

  $scope.fn_toggle_feed = function() {
    console.log('toggle feed');
    command = {
      'type': 'set_recipe',
      'key': 'SERVICE_FUNC_NO_FEEDER',
      'value': !$scope.remote_data.recipe.SERVICE_FUNC_NO_FEEDER,
    }
    ws.get(command);
  }

  $scope.fn_reset_counter = function() {
    console.log('reset counter');
    command = {
      'type': 'reset_counter',
    }
    ws.get(command);
  }

  $scope.fn_clear_error = function(error) {
    console.log('clear error:', error.error_id);
    command = {
      'type': 'clear_error',
      'error_id': error.error_id,
    }
    ws.get(command);
  }


  $scope.fn_log = console.log;
  $scope.moment = moment;
  // ------------- bootstrap -------------
  initialize();


});


// ------------- disable template caching -------------

app.run(function($rootScope, $templateCache) {
  $rootScope.$on('$viewContentLoaded', function() {
    $templateCache.removeAll();
  });
});
