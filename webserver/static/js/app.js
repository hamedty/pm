var app = angular.module('app', ['ngWebSocket']);

app.factory('ws', function($websocket) {
  // Open a WebSocket connection
  var dataStream = $websocket("ws://" + location.host + "/ws");

  var methods = {
    onMessage: function(cb) {
      dataStream.onMessage(cb)
    },
    get: function(data) {
      dataStream.send(JSON.stringify(data));
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
        $scope.nodes[3].selected = true;
        break;
      case 'status_update':
        $scope.update_node_status(message.payload);
        break;
      default:
        console.log(message);
    }
  });
  $scope.update_node_status = function(nodes_status) {
    // now = Date.parse(new Date()) / 1000.
    // nodes_status.forEach(x => {
    //   delete x.age;
    // })
    $scope.nodes_status = nodes_status;
  }

  $scope.send_command = function(command) {
    data = {
      command: command,
    }
    ws.get(data);
  }

  $scope.command_text_area = COMMAND_TEMPLATE_ALIGN_HOLDER; //"";

  $scope.COMMAND_TEMPLATES = {
    'set valve': COMMAND_TEMPLATE_SET_VALVE,
    'home motor': COMMAND_TEMPLATE_HOME_AXIS,
    'move motors': COMMAND_TEMPLATE_MOVE_MOTORS,
    'dump frame': COMMAND_TEMPLATE_DUMP_FRAME,
    'dump training holder': COMMAND_TEMPLATE_DUMP_TRAINING_HOLDER,
    'align holder': COMMAND_TEMPLATE_ALIGN_HOLDER,

  }
  $scope.select_template = function(name) {
    $scope.command_text_area = $scope.COMMAND_TEMPLATES[name];
  }

  $scope.submit_form = function() {
    data = $scope.command_text_area;
    data.replace(/\n/g, " ");
    data = 'new Object(' + data + ')';
    data = {
      form: eval(data),
      selected_nodes: $scope.nodes.filter(x => x.selected).map(x => x.name),
    }
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


COMMAND_TEMPLATE_SET_VALVE = "{\n\
    'verb': 'set_valves',\n\
    'valves': [0],\n\
}";

COMMAND_TEMPLATE_HOME_AXIS = "{\n\
    'verb': 'home',\n\
    'axis': 0,\n\
}";



COMMAND_TEMPLATE_MOVE_MOTORS = "{\n\
    'verb': 'move_motors',\n\
    'moves': [\n\
        [0, 250, 0],\n\
        [0, 250, 0],\n\
        [0, 250, 0],\n\
        [500, 250, 0],\n\
    ]\n\
}"

COMMAND_TEMPLATE_DUMP_FRAME = "{'verb': 'dump_frame'}"
COMMAND_TEMPLATE_DUMP_TRAINING_HOLDER = "{\n\
  'verb': 'dump_training_holder',\n\
  'revs': 1,\n\
  'frames_per_rev': 400,\n\
}"
COMMAND_TEMPLATE_ALIGN_HOLDER = "{'verb': 'align_holder'}"
