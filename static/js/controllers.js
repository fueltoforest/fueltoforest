var module = angular.module('fuelToForestControllers', []);

module.controller('LoginController', ["$scope", "$http", "$window", "$location",
    function ($scope, $http, $window, $location) {

        $scope.login = function () {
            $http.post("/login", {
                email: $scope.email,
                password: $scope.password
            }).success(function (data) {
                    $window.sessionStorage.token = data.token;
                    $location.path("/");
                })
        };

    }]);

module.controller('RegisterController', ["$scope", "$http", "$window", "$location",
    function ($scope, $http, $window, $location) {
        $scope.user = {};
        $scope.register = function () {
            $http
                .post("/register", $scope.user)
                .success(function (data) {
                    $window.sessionStorage.token = data.token;
                    $location.path("/")
                });
        };
    }]);


module.controller('HeartbeatController', ["$scope", "$http", "$window", "$location", "geolocation",
    function ($scope, $http, $window, $location, geolocation) {

        $scope.heartbeat = function (ride_id) {
            geolocation.getLocation().then(function (data) {
                var coordinates = [
                    data.coords.longitude,
                    data.coords.latitude
                ];
                $http.post("rides/" + ride_id + "/heartbeat", {
                    "location": coordinates
                }).success(function () {
                    setTimeout(function () {
                        $scope.heartbeat(ride_id);
                    }, 3000);
                })
            });
        };

        $scope.finish = function () {

            geolocation.getLocation().then(function (data) {
                var coordinates = [
                    data.coords.longitude,
                    data.coords.latitude
                ];
                $http.post("rides/" + $scope.ride_id + "/finish", {
                    "location": coordinates
                }).success(function () {
                    $location.path("/");
                })
            });


        };

        geolocation.getLocation().then(function (data) {
            var coordinates = [
                data.coords.longitude,
                data.coords.latitude
            ];
            $http.post("/rides", {
                "start_location": coordinates
            }).success(function (data) {
                $scope.ride_id = data.ride_id;
                $scope.heartbeat(data.ride_id);
            });
        });

    }]);

module.controller('RidesController', ["$scope", "$http", "$window", "$location",
    function ($scope, $http, $window, $location) {
        //$scope.user = $window.localStorage.user;
    }]);
