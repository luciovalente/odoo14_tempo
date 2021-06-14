odoo.define('syd_bit2win.test2_client_action', function (require) {
'use strict';


var core = require('web.core');
var Widget = require('web.Widget');
var AbstractAction = require('web.AbstractAction');

var QWeb = core.qweb;

var Test2ClientAction = AbstractAction.extend( {
	template: 'syd_bit2win_test_2',
    events: {
    	

    },

    /**
     * @override
     */
    init: function (parent, action) {
        this._super.apply(this, arguments);
        this.action_manager = parent;
        this.action = action;
        document.addEventListener('avatarSelected', function popup(e) {
        	alert('HTML Event Recieved: ' + e.detail);
        	});
    },
    start: function () {
        this._super.apply(this, arguments);
        
    },
    renderElement: function () {
    	this._super.apply(this, arguments);
    	
        
        
    },

});

core.action_registry.add('syd_bit2win.test2_client_action', Test2ClientAction);

return Test2ClientAction;

});
