odoo.define('syd_web_pin_map.Model', function (require) {
"use strict";

const AbstractModel = require('web.AbstractModel');
const session = require('web.session');
const core = require('web.core');
const _t = core._t;

const MapModel = AbstractModel.extend({

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @constructor
     */
    init: function () {
        this._super.apply(this, arguments);
        this.data = {};
    },

    __get: function () {
        return this.data;
    },

    canRMBClick: function() {
        return this._rpc({
            model: this.loadParams.fieldsInfo[this.loadParams.locationsFieldName].relation,
            method: 'check_access_rights',
            kwargs: {operation: 'write', raise_exception: false},
        });
    },

    __load: function (params) {
        this.data.count = 0;
        this.data.offset = 0;
        this.data.limit = params.limit;
        this.data.shouldUpdatePosition = false;
        this.canRMBClick().then(function (ar) {
            this.data.canRMBClick = ar;
        }.bind(this));

        return this._fetchData();
    },

    __reload: function (handle, params) {
        const options = params || {};
        if (options.domain !== undefined) {
            this.domain = options.domain;
        }
        if (options.limit !== undefined) {
            this.data.limit = options.limit;
        }
        if (options.offset !== undefined) {
            this.data.offset = options.offset;
        }
        this.data.shouldUpdatePosition = true;
        return this._fetchData();
    },

    _fetchData: async function () {
        // INFO: fetches main records.
        const results = await this._rpc({
            method: 'search_read',
            model: this.loadParams.modelName,
            context: this.loadParams.context,
            // INFO: builds string fields list from levelFields object.
            // fields: this.levelFieldsInfo.map(f => { return f.fieldName }),
            fields: Object.keys(this.loadParams.levelFieldsInfo),
            domain: this.loadParams.domain,
            orderBy: this.loadParams.orderBy,
            limit: this.data.limit,
            offset: this.data.offset
        });

        this.data.records = results;
        this.data.count = results.length;

        let locationIds = [];
        // INFO: extracts itemsField ids.
        this.data.records.forEach(record => {
            locationIds = locationIds.concat(record[this.loadParams.locationsFieldName]);
        });
        locationIds = _.uniq(locationIds);
        // INFO: loads itemsField ids record.
        let items = locationIds.length ? await this._fetchItems(this.loadParams.fieldsInfo[this.loadParams.locationsFieldName].relation, locationIds) : [];

        // INFO: loops thru data.records to fill up items data collected above.
        this.data.records.forEach((record) => {
            record[this.loadParams.locationsFieldName].forEach((ai, index) => {
                // INFO: matches item records just fetched above.
                items.forEach((item) => {
                    if (ai === item.id) {
                        record[this.loadParams.locationsFieldName][index] = item;
                    }
                });
            });
        });

        return results;
    },
    _fetchItems: function (relation, ids) {
        return this._rpc({
            model: relation,
            method: 'search_read',
            domain: [['id', 'in', ids]],
            // INFO: builds string fields list from locationFields object.
            // fields: this.locationFieldsInfo.map(f=>{ return f.fieldName }),
            fields: Object.keys(this.loadParams.locationFieldsInfo),
        });
    },
});

return MapModel;

});
