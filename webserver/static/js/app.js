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
  ws.onMessage(function(message) {
    console.log(JSON.parse(message.data));
    $scope.nodes = JSON.parse(message.data);
  });
  $scope.send_command = function(command) {
    data = {
      command: command,
    }
    ws.get(data);
  }

  $scope.nodes = []
  $scope.select_node = function(node) {
    node.selected = !node.selected;
  }

  $scope.selected_nodes_string = function() {
    return $scope.nodes.filter(x => x.selected).map(x => x.name).join(', ')
  }
});



app.run(function($rootScope, $templateCache) {
  $rootScope.$on('$viewContentLoaded', function() {
    $templateCache.removeAll();
  });
});