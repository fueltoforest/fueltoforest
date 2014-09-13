var module = angular.module('fuelToForestApp', [
  'ngRoute',
  'fuelToForestControllers'
]);


module.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.
      when('/login', {
        templateUrl: '/static/partial-templates/login.html',
        controller: 'LoginController'
      }).
      when('/register', {
        templateUrl: '/static/partial-templates/register.html',
        controller: 'RegisterController'
      }).
      otherwise({
        redirectTo: '/login'
      });
}]);
