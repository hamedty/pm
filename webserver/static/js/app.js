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
    message = JSON.parse(message.data)
    switch (message.type) {
      case 'architecture':
        $scope.nodes = message.payload;
        break;
      case 'status_update':
        $scope.nodes_status = message.payload;
        break;
      default:
        console.log(message);
    }
  });

  $scope.send_command = function(command) {
    data = {
      command: command,
    }
    ws.get(data);
  }

  $scope.command_text_area = "{\n\
          'verb': 'set_valves',\n\
          'valves': [0],\n\
}";

  $scope.submit_form = function() {
    data = $scope.command_text_area;
    data.replace(/\n/g, " ");
    data = 'new Object(' + data + ')';
    data = eval(data);
    console.log(data)
    ws.get(data);
  }
  $scope.nodes = []
  $scope.select_node = function(node) {
    node.selected = !node.selected;
  }

  $scope.selected_nodes_string = function() {
    return $scope.nodes.filter(x => x.selected).map(x => x.name).join(', ')
  }
  $scope.selected_nodes_actions = function() {
    return $scope.nodes.filter(x => x.selected).map(x => x.actions)
  }
});



app.run(function($rootScope, $templateCache) {
  $rootScope.$on('$viewContentLoaded', function() {
    $templateCache.removeAll();
  });
});
