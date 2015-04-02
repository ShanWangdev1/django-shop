(function(angular, undefined) {
'use strict';

// module: django.shop, TODO: move this into a summary JS file
var djangoShopModule = angular.module('django.shop.checkout', []);


// Shared controller for the checkout view, used to update the cart, and optionally, if
// all forms are valid, proceed. Since this controller does not make any presumption on how
// and where to proceed to, the caller has to set the controllers `deferred` to a `$q.deferred()`
// object.
djangoShopModule.controller('CheckoutCtrl', ['$scope', '$http', '$q', 'djangoUrl', 'djangoForm',
                                             function($scope, $http, $q, djangoUrl, djangoForm) {
	var self = this, updateURL = djangoUrl.reverse('shop-api:checkout-update');
	this.isLoading = true;  // prevent premature updates and re-triggering
	$scope.update = update;

	function update(deferred) {
		if (self.isLoading)
			return;
		self.isLoading = true;
		$http.post(updateURL, $scope.data).success(function(response) {
			var hasErrors = false;
			console.log(response);
			if (deferred) {
				// only report errors, when the customer wishes to proceed
				angular.forEach(response.errors, function(errors, key) {
					hasErrors = djangoForm.setErrors($scope[key], errors) || hasErrors;
				});
				if (true || hasErrors) {
					deferred.notify(response.errors);
				} else {
					deferred.resolve();
				}
			}
			delete response.errors;
			$scope.cart = response;
		}).error(function(msg) {
			console.error("Unable to update checkout forms: " + msg);
		})['finally'](function() {
			self.isLoading = false;
		});
	}

	this.registerButton = function(element) {
		var deferred = $q.defer();
		element.on('click', function() {
			update(deferred);
		});
		element.on('$destroy', function() {
			element.off('click');
		});
		return deferred.promise;
	};

}]);


// Directive <form shop-checkout-form> (must be added as attribute to the <form> element)
// It is used to handle updates on the checkout forms.
djangoShopModule.directive('shopCheckoutForm', function() {
	return {
		restrict: 'A',
		controller: 'CheckoutCtrl',
		link: function(scope, element, attrs, CheckoutCtrl) {
			CheckoutCtrl.isLoading = false;
		}
	};
});


djangoShopModule.directive('shopCheckoutProceed', ['$window', function($window) {
	return {
		restrict: 'EA',
		controller: 'CheckoutCtrl',
		link: function(scope, element, attrs, CheckoutCtrl) {
			CheckoutCtrl.isLoading = false;
			CheckoutCtrl.registerButton(element).then(function() {
				console.log("Proceed to: " + attrs.action);
				//$window.location.href = attrs.action;
			}, null, function(errs) {
				console.error("The checkout form contains errors.");
				console.log(errs);
			});
		}
	};
}]);


djangoShopModule.directive('shopPurchaseButton', ['$window', '$http', '$q', 'djangoUrl',
                                                  function($window, $http, $q, djangoUrl) {
	var purchaseURL = djangoUrl.reverse('shop-api:checkout-purchase');
	return {
		restrict: 'EA',
		controller: 'CheckoutCtrl',
		link: function(scope, element, attrs, CheckoutCtrl) {
			var isLoading = false;
			CheckoutCtrl.isLoading = false;
			CheckoutCtrl.registerButton(element);
			// build a deferred object to proceed with the buttons action
			CheckoutCtrl.deferred = $q.defer();
			CheckoutCtrl.deferred.promise.then(function() {
				// the next step finally converts the cart into an order object
				return $http.post(purchaseURL, scope.data);
			}).then(function(response) {
				console.log(response);
				console.log("puchased");
				return CheckoutCtrl.deferred.promise;
			}, function(msg) {
				console.error("Unable purchase cart items: " + msg);
//			})['finally'](function() {
//				isLoading = false;
			});
		}
	};
}]);

})(window.angular);
