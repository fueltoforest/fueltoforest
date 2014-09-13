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

module.controller('RidesController', ["$scope", "$http", "$window", "$location",
    function ($scope, $http, $window, $location) {
        //$scope.user = $window.localStorage.user;
}]);
