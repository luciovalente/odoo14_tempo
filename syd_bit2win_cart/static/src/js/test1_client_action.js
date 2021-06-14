odoo.define('syd_bit2win_cart.test1_client_action', function (require) {
'use strict';


var core = require('web.core');
var Widget = require('web.Widget');
var AbstractAction = require('web.AbstractAction');

var QWeb = core.qweb;

var Test1ClientAction = AbstractAction.extend( {
	template: 'care_template',
    events: {
    	

    },

    /**
     * @override
     */
    init: function (parent, action) {
        this._super.apply(this, arguments);
        this.action_manager = parent;
        this.action = action;
    },
    start: function () {
        this._super.apply(this, arguments);
        
    },
    renderElement: function () {
    	this._super.apply(this, arguments);
    	
        
        
    },

});

core.action_registry.add('syd_bit2win_cart.test1_client_action', Test1ClientAction);

return Test1ClientAction;

});
