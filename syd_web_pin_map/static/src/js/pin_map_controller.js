odoo.define('syd_web_pin_map.Controller', function (require) {
"use strict";

const AbstractController = require('web.AbstractController');
const core = require('web.core');
const qweb = core.qweb;

const MapController = AbstractController.extend({
    custom_events: _.extend({}, AbstractController.prototype.custom_events, {
        'pin_clicked': '_onPinClick',
        'open_clicked': '_onOpenClicked',
        'new_clicked': '_onNewClicked',
        'pager_changed': '_onPagerChanged',
    }),
    /**
     * @constructor
     */
    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
    },
    /**
     * @override
     * @param {jQuery} [$node]
     */
    renderButtons: function ($node) {
        this.$buttons = $(qweb.render("syd_web_pin_map.buttons"), { widget: this });
        // this.$buttons.find('.pin_map_add_new').on('click', e => {
        //     if ($('.o_map_container').css('cursor') === 'crosshair')
        //         $('.o_map_container').css('cursor', 'crosshair');
        //     $('.o_map_container').css('cursor', 'grab');
        //
        // });
        // on('click', e => {
        //     if ($('.o_map_container').css('cursor') === 'crosshair')
        //         this.trigger('new_clicked', {
        //             latitude: self.latitude,
        //             longitude: self.longitude,
        //             floor_id: self.floor_id,
        //             responsible_id: self.responsible_id,
        //         });
        // })
        if ($node)
            this.$buttons.appendTo($node);
    },
    update: async function () {
        await this._super(...arguments);
        this._updatePaging();
    },
    /**
     * Return the params (currentMinimum, limit and size) to pass to the pager,
     * according to the current state.
     *
     * @private
     * @returns {Object}
     */
    _getPagingInfo: function () {
        const state = this.model.get();
        return {
            currentMinimum: state.offset + 1,
            limit: state.limit,
            size: state.count,
        };
    },
    /**
     * Redirects to views when clicked on open button in pin popup.
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onOpenClicked: function (ev) {
        this.do_action({
            type: 'ir.actions.act_window',
            views: [[false, 'form']],
            target: 'current',
            res_model: this.model.loadParams.locationRelationModelName,
            res_id: ev.data.id,
        });
    },
    _onNewClicked: function (ev) {
        let context = {}
        for (let def in this.model.loadParams.locationDefaultFieldsInfo) {
            context['default_' + def] = ev.data[this.model.loadParams.locationDefaultFieldsInfo[def]];
        }
        context['default_' + this.model.loadParams.locationRelationFieldName] = ev.data.level_id;
        this.do_action({
            type: 'ir.actions.act_window',
            views: [[false, 'form']],
            target: 'current',
            res_model: this.model.loadParams.locationRelationModelName,
            res_id: false,
            context: context
        });
    },
    async _onPagerChanged(ev) {
        const { currentMinimum, limit } = ev.data;
        await this.reload({ limit, offset: currentMinimum - 1 });
    },
});

return MapController;

});
