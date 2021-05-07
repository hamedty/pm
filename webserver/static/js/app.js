var app = angular.module('app', ['ngWebSocket']);

app.factory('ws', function($websocket) {
  // Open a WebSocket connection
  var dataStream = $websocket("ws://" + location.host + "/ws");

  var methods = {
    onMessage: function(cb) {
      dataStream.onMessage(cb)
    },
    get: function(data) {
      dataStream.send(JSON.stringify({
        data
      }));
    }
  };

  return methods;
})

app.controller('app_controller', function($scope, ws) {
  console.log('ws:', ws);
  ws.onMessage(function(message) {
    console.log(message);
    $scope.m = JSON.parse(message.data);
  });
  $scope.send_command = function(command) {
    data = {
      command: command,
    }
    ws.get(data);
  }
});



app.run(function($rootScope, $templateCache) {
  $rootScope.$on('$viewContentLoaded', function() {
    $templateCache.removeAll();
  });
});