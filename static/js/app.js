var module = angular.module('fuelToForestApp', [
    'ngRoute',
    'fuelToForestControllers'
]);


module.config(['$routeProvider',
    function ($routeProvider) {
        $routeProvider.
            when('/', {
                templateUrl: '/static/partial-templates/rides.html',
                controller: 'RidesController'
            }).
            when('/login', {
                templateUrl: '/static/partial-templates/login.html',
                controller: 'LoginController'
            }).
            when('/register', {
                templateUrl: '/static/partial-templates/register.html',
                controller: 'RegisterController'
            }).
            otherwise({
                redirectTo: '/'
            });
    }]);

module.factory('authInterceptor', function ($rootScope, $q, $window, $location) {
    return {
        request: function (config) {
            config.headers = config.headers || {};
            if ($window.sessionStorage.token) {
                config.headers.token = $window.sessionStorage.token;
            }

            return config;
        },
        'responseError': function (rejection) {
            // do something on error

            if (rejection.status == 401) {
                $location.path("/login")
            }

            return $q.reject(rejection);
        }
    };
});

module.config(function ($httpProvider) {
    $httpProvider.interceptors.push('authInterceptor');
});

module.run(['$rootScope', '$window', '$http', function($rootScope, $window, $http) {
    $http.post("/authenticate", {
        "token": $window.sessionStorage.token
    }).success(function (data) {
        $rootScope.user = data;
    })
}]);
