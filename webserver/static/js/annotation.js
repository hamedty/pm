var annotation_app = angular.module('annotation_app', []);

annotation_app.controller('annotation_controller', function($scope, $http) {
  $scope.components = ["Holder", "Dosing"];
  $scope.stations = Array.from(Array(10).keys()).map(function(x){return x+101});
  $scope.component = "Holder"
  $scope.station = 103
  $scope.$watch('component', function() {fetch();});
  $scope.$watch('station', function() {fetch();});
  // http://localhost:8080/annotation/api?component=dosing&node=101
  function fetch(){
    if (!$scope.component) return;
    if (!$scope.station) return;
    $http.get("/annotation/api?component=" + $scope.component.toLowerCase() + "&station=" + $scope.station)
    .then(function(response){
      data_received(response.data);
    });
  }
  function post(data){
    $http.post("/annotation/api?component=" + $scope.component.toLowerCase() + "&station=" + $scope.station, data)
    .then(function(response){
      data_received(response.data);
    });
  }
  $scope.update = function(e) {
    post({
      sets:$scope.sets,
      roi:$scope.roi,
    });
  };

  function data_received(data) {
    // console.log(data);
    $scope.sets = data.sets;
    $scope.roi = data.roi;
    $scope.reference_id = $scope.component+$scope.station;
  }
});

annotation_app.directive('graph', function(){
  function draw(scope, canvas, id, zero) {
    var ctx = canvas.getContext('2d');
    var scale = 2.0
    ctx.canvas.width  = scope.roi.dx*scale;
    ctx.canvas.height = scope.roi.dy*scale;
    ctx.fillStyle = "black";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    var image = new Image();
    var url;
    if (id=='reference') {
      url = '/dataset/reference/'+scope.component.toLowerCase()+'_192.168.44.'+scope.station+'.png';
    } else {
      zero = String(zero).padStart(3, '0')
      url = '/dataset/'+scope.component.toLowerCase()+'_'+scope.station+'_' + id + '_192.168.44.'+scope.station+'/'+zero+'_00.png';
    }
    image.src = url;
    image.onload = function(){
        ctx.drawImage(image,
            scope.roi.x0, scope.roi.y0,   // Start at 70/20 pixels from the left and the top of the image (crop),
            scope.roi.dx, scope.roi.dy,   // "Get" a `50 * 50` (w * h) area from the source image (crop),
            0, 0,     // Place the result at 0, 0 in the canvas,
            scope.roi.dx*scale, scope.roi.dy*scale); // With as width / height: 100 * 100 (scale)
            ctx.beginPath();
            if (scope.component.toLowerCase() == 'dosing'){
              ctx.moveTo(0, scope.roi.dy/2*scale);
              ctx.lineTo(scope.roi.dx*scale, scope.roi.dy/2*scale);

            }
            else {
              ctx.moveTo(scope.roi.dx/2*scale, 0);
              ctx.lineTo(scope.roi.dx/2*scale, scope.roi.dy*scale);
            }
            ctx.strokeStyle = "red";
            ctx.stroke();
    }


  }
  return {
      restrict: 'E',
      template: '<canvas></canvas>',
      link: function(scope, elm, attrs, ctrl) {
       draw(scope, elm.children()[0], attrs.id, attrs.zero);
       scope.$watch(function() {
         return JSON.stringify(elm.attr('zero')) + JSON.stringify(elm.attr('roi'));
       }
         ,function(newValue,oldValue) {
           if(!newValue) return
           if (newValue != oldValue)
           draw(scope, elm.children()[0], attrs.id, attrs.zero);
        });
      }

  }
});
