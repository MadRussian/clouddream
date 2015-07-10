/*
 * angular-deckgrid-demo
 *
 * Copyright(c) 2013 André König <akoenig@posteo.de>
 * MIT Licensed
 *
 */

/**
 * @author André König (andre.koenig@posteo.de)
 */

angular.module('akoenig.deckgrid.demo').controller('HomeController', [
  '$scope',
  '$http',
  '$location',

  function initialize ($scope,$http,$location) {
    'use strict';

    var url = '/content/images.json';

    var searchObject = $location.search();
    var N = searchObject.N || 20;
    N = Math.max(Math.min(N,100),1);

    $http.get(url).success(function(data) {
      if (searchObject.latest) {
        $scope.photos = data.slice(-N);
        $scope.photos = $scope.photos.reverse();
      } else {
        $scope.photos = _.sample(data,N);
      }
    }).error(function() {
      $scope.photos = [];
    });
  }
]);
