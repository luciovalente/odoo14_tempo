odoo.define('syd_web_pin_map.View', function (require) {
"use strict";

const PinMapModel = require('syd_web_pin_map.Model');
const PinMapController = require('syd_web_pin_map.Controller');
const PinMapRenderer = require('syd_web_pin_map.Renderer');
const AbstractView = require('web.AbstractView');
const RendererWrapper = require('web.RendererWrapper');
const utils = require('web.utils');
const viewRegistry = require('web.view_registry');
const _t = require('web.core')._t;

const PinMapView = AbstractView.extend({
    jsLibs: [
        '/syd_web_pin_map/static/lib/extra/csvparser.js',
        '/syd_web_pin_map/static/lib/extra/jquery.mousewheel.js',
        '/syd_web_pin_map/static/lib/extra/magnific-popup.js',
        '/syd_web_pin_map/static/lib/mapplic/mapplic.js',
    ],
    cssLibs: [
        '/syd_web_pin_map/static/lib/mapplic/mapplic.css',
        '/syd_web_pin_map/static/src/css/pin_map.css'
    ],
    config: _.extend({}, AbstractView.prototype.config, {
        Model: PinMapModel,
        Controller: PinMapController,
        Renderer: PinMapRenderer,
    }),
    icon: 'fa-map-marker',
    display_name: 'Pin Map',
    viewType: 'pin_map',
    mobile_friendly: true,
    searchMenuTypes: [],
    // INFO: hides searchbar in the control panel.
    withSearchBar: false,

    init: function (viewInfo, params) {
        this._super.apply(this, arguments);

        const levelFieldsInfo = [];
        const locationFieldsInfo = [];
        const locationDefaultFieldsInfo = {};

        this.rendererParams.user_id = this.loadParams.context.uid;
        this.rendererParams.mapWidth = parseInt(this.arch.attrs.width) || 1000;
        this.rendererParams.mapHeight = parseInt(this.arch.attrs.height) || 1000;

        if (this.arch.attrs.default_order) {
            this.loadParams.orderBy = [{ name: this.arch.attrs.default_order || 'display_name', asc: true }];
        }
        this.rendererParams.defaultOrder = this.arch.attrs.default_order;

        // INFO: hides pager info on the control panel.
        this.loadParams.limit = 0;

        // INFO: builds needed data from pin_map arch xml views.
        let tag_level = this.arch.children.find((i)=>i.tag === 'levels')
        let tag_level_location = tag_level.children.find((i)=>i.tag === 'locations')
        let tag_level_location_default = tag_level_location.children.find((i)=>i.tag === 'default')
        tag_level.children.forEach(node => {
            if (node.tag && node.attrs.field)
                levelFieldsInfo[node.attrs.field] = {
                    target: node.tag,
                    string: node.attrs.string || '',
                };
        });
        tag_level_location.children.forEach(node => {
            if (node.tag && node.attrs.field)
                locationFieldsInfo[node.attrs.field] = {
                    target: node.tag,
                    string: node.attrs.string || '',
                };
        });
        tag_level_location_default.children.forEach(node => {
            if (node.tag && node.attrs.field)
                locationDefaultFieldsInfo[node.attrs.field] = node.attrs.from;
        });

        // INFO: if no locationsFieldsInfo defined then returns empty records data.
        if (!levelFieldsInfo || !locationFieldsInfo) {
            throw new Error("Some missing Web Pin Map XML parameters.");
        }

        this.loadParams.fieldsInfo = this.fields;

        this.loadParams.locationsFieldName = tag_level_location.attrs.field;
        this.loadParams.locationRelationModelName = this.fields[tag_level_location.attrs.field].relation;
        this.loadParams.locationRelationFieldName = this.fields[tag_level_location.attrs.field].relation_field;
        this.loadParams.levelFieldsInfo = levelFieldsInfo;
        this.loadParams.locationFieldsInfo = locationFieldsInfo;
        this.loadParams.locationDefaultFieldsInfo = locationDefaultFieldsInfo;

        this.rendererParams.locationsFieldName = this.loadParams.locationsFieldName
        this.rendererParams.locationRelationFieldName = this.loadParams.locationRelationFieldName
        this.rendererParams.levelFieldsInfo = this.loadParams.levelFieldsInfo;
        this.rendererParams.locationFieldsInfo = this.loadParams.locationFieldsInfo;
        this.rendererParams.hasFormView = params.actionViews.some(view => view.type === "form");
    },
    /**
     * @override
     */
    getRenderer(parent, state) {
        state = Object.assign({}, state, this.rendererParams);
        return new RendererWrapper(null, this.config.Renderer, state);
    },
});

viewRegistry.add('pin_map', PinMapView);

return PinMapView;

});
