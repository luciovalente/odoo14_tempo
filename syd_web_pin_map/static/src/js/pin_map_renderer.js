odoo.define('syd_web_pin_map.Renderer', function (require) {
    "use strict";

    var config = require('web.config');
    const AbstractRendererOwl = require('web.AbstractRendererOwl');

    const { useRef, useState } = owl.hooks;

    const colors = [
        '#F06050',
        '#6CC1ED',
        '#F7CD1F',
        '#814968',
        '#30C381',
        '#D6145F',
        '#475577',
        '#F4A460',
        '#EB7E7F',
        '#2C8397',
    ];

    class MapRenderer extends AbstractRendererOwl {
        /**
         * @constructor
         */
        constructor() {
            super(...arguments);
            this.map = null;
            this.pins = [];
            this.state = useState({});
            this.x = false;
            this.y = false;
            this.level_id = this.props.records[0].id;
            this.user_id = this.props.user_id;
            this.mapContainerRef = useRef('mapContainer');
        }F
        /**
         * Load pin icons.
         *
         * @override
         */
        async willStart() {
            const p = { method: 'GET' };
            [this._pinCircleSVG, this._pinNoCircleSVG] = await Promise.all([
                this.env.services.httpRequest('syd_web_pin_map/static/img/pin-circle.svg', p, 'text'),
                this.env.services.httpRequest('syd_web_pin_map/static/img/pin-no-circle.svg', p, 'text'),
            ]);
            return super.willStart(...arguments);
        }
        /**
         * Builds Mapplic map.
         *
         * @private
         */
        _buildMapplicMap() {
            const self = this;
            let css = '.mapplic-filtered svg [id^=landmark] > * {opacity: 1 !important; }';
            this.map_options = {
                source: this._buildMap(),
                customcss: css,
                sidebar: true,
                height: '100%',
                maxheight: 'inherited',
                search: true,
                searchdescription: true,
                searcheverywhere: true,
                minimap: false,
                marker: 'default',
                fillcolor: true,
                fullscreen: true,
                developer: false,
                thumbholder: true,
                maxscale: 5,
                iconfile: '/syd_web_pin_map/static/lib/mapplic/images/icons.svg'
            };
            this.$map = $('.o_map_container').mapplic(this.map_options);
            this.map = this.$map.data('mapplic');
            this.$mapplicMap = this.$map.find('.mapplic-map');
            this.$contextMenu = $('.o_pin_map_context_menu');

            // INFO: binds showing of context menu when right mouse button is pressed on the map.
            this.$map.unbind().bind("contextmenu", function (e) {
                e.preventDefault();
                self.$contextMenu.finish().toggle(100).
                    // INFO: Catches mouse position to show context menu in the right position.
                    css({
                        top: e.pageY - $(self.el).offset().top + "px",
                        left: e.pageX - $(self.el).offset().left + "px"
                    });
            }).on('mousemove', function (e) {
                // INFO: on mouse movements saves right x & y to use them when creating new pin for example.
                let x, y;
                let scale;

                if (self.$mapplicMap) {
                    let offset = self.$mapplicMap.offset();

                    x = (e.pageX - offset.left) / self.$mapplicMap.width();
                    y = (e.pageY - offset.top) / self.$mapplicMap.height();
                    scale = self.map.scale;
                }

                self.x = x ? (x / scale).toFixed(4) : null;
                self.y = y ? (y / scale).toFixed(4) : null;

                // $(self.el).find('.o_map_debug').html(
                //     `<h6>X / Y = ${self.x} / ${self.y}</h6>` +
                //     `<h6>Scale = ${scale}</h6>`
                // );
            });

            // INFO: clicked somewhere else but map? If so hides contextmenu just in case.
            $(document).bind("mousedown", function (e) {
                // INFO: if clicked element is not the menu.
                if (!$(e.target).parents(".o_pin_map_context_menu").length > 0) {
                    $(".o_pin_map_context_menu").hide(100);
                }
            });

            // INFO: a contextmenu element is clicked.
            if (this.props.canRMBClick)
                this.$contextMenu.find("li").click(function (e) {
                    // INFO: this is the triggered action name.
                    switch ($(this).attr("data-action")) {
                        case "add_new_asset":
                            self.trigger('new_clicked', {
                                level_id: self.level_id,
                                user_id: self.user_id,
                                x: self.x,
                                y: self.y,
                            });
                            break;
                    }
                    // INFO: hides it after action was triggered.
                    $(".o_pin_map_context_menu").hide(100);
                });
            // INFO: in case user switches level then saves the value to use it later.
            this.$map.on('levelswitched', function (e, level) {
                self.level_id = parseInt(level);
            });
        }
        /**
         * Builds map level object from passed records.
         *
         * @private
         */
        _buildLevel(recLev) {
            let result = {}
            for (const field of Object.keys(this.props.levelFieldsInfo)) {
                let fld = this.props.levelFieldsInfo[field];
                if (fld.target)
                    result[fld.target] = recLev[field]
            }
            result.locations = []
            for (const rec of recLev[this.props.locationsFieldName]) {
                let locs = {}
                for (const field of Object.keys(this.props.locationFieldsInfo)) {
                    let fld = this.props.locationFieldsInfo[field];
                    if (fld.target)
                        locs[fld.target] = rec[field]
                }
                result.locations.push(locs)
            }
            return result;
        }
        /**
         * Builds map from props.records.
         *
         * @private
         */
        _buildMap() {
            let result = {
                mapwidth: this.props.mapWidth,
                mapheight: this.props.mapHeight,
                levels: []
            }
            for (const recLev of this.props.records) {
                result.levels.push(this._buildLevel(recLev))
            }
            return result;
        }
        /**
         * Initialize and mount map.
         *
         * @override
         */
        mounted() {
            if (!this.props.shouldUpdatePosition)
                this._buildMapplicMap();
            this._updateMap();
            super.mounted(...arguments);
        }
        /**
         * Update pins position in the map.
         *
         * @private
         */
        _updateMap() {
            if (this.props.shouldUpdatePosition) {
                let fp = this._buildMap();
                let l = fp.levels.find(l => l.id == this.map.level);
                this.map.addLocations(l.locations, l.id);
                this.map.container.resetZoom();
            }
            // this._addPins();
        }
        /**
         * Update pins position in the map.
         *
         * @override
         */
        patched() {
            this._updateMap();
            super.patched(...arguments);
        }
        /**
         * Remove map and the listeners on its pins.
         *
         * @override
         */
        willUnmount() {
            for (const pin of this.pins) {
                pin.off('click');
            }
            // if (this.map)
            //     this.$map.remove()
            super.willUnmount(...arguments);
        }
        /**
         * If there's located records, adds the corresponding pin on the map.
         * Binds events to the created pins.
         *
         * @private
         */
        _addPins() {
            this._removePins();

            const pinsInfo = {};
            let records = this.props.records;
            for (const record of records) {
                for (const item of record.asset_item_ids) {
                    if (item && item.latitude && item.longitude) {
                        const key = `${item.latitude}-${item.longitude}`;
                        if (key in pinsInfo) {
                            pinsInfo[key].record = item;
                            pinsInfo[key].ids.push(item.id);
                        } else {
                            pinsInfo[key] = { record: item, ids: [item.id] };
                      }
                    }
                }
            }

            for (const pinInfo of Object.values(pinsInfo)) {
                // INFO: loads data to use into template syd_web_pin_map.pin.
                const params = {
                    count: pinInfo.ids.length,
                    isMulti: pinInfo.ids.length > 1,
                    number: this.props.records.indexOf(pinInfo.record) + 1,
                    numbering: this.props.numbering,
                    pinSVG: (this.props.numbering ? this._pinNoCircleSVG : this._pinCircleSVG),
                };

                // INFO: data for pins icon.
                const iconInfo = {
                    className: 'o_map_pin',
                    html: this.env.qweb.renderToString('syd_web_pin_map.pin', params),
                };

                // Attach pin with icon and popup
                const pin = L.pin([
                    pinInfo.record.latitude,
                    pinInfo.record.longitude
                ], { icon: L.divIcon(iconInfo) });

                pin.addTo(this.map);

                pin.on('click', () => {
                    this._createPinPopup(pinInfo);
                });

                this.pins.push(pin);
            }
        }
        /**
         * Create a popup for the specified pin.
         *
         * @private
         * @param {Object} pinInfo
         */
        _createPinPopup(pinInfo) {
            const popupFields = this._getPinPopupFields(pinInfo);
            const ai = pinInfo.record;
            const popupHtml = this.env.qweb.renderToString('syd_web_pin_map.pinPopup', {
                fields: popupFields,
                hasFormView: this.props.hasFormView,
                // url: `https://www.google.com/maps/dir/?api=1&destination=${partner.partner_latitude},${partner.partner_longitude}`,
            });

            const popup = L.popup({ offset: [0, -30] })
                .setLatLng([ai.latitude, ai.longitude])
                .setContent(popupHtml)
                .openOn(this.map);

            const openBtn = popup.getElement().querySelector('button.o_open');
            if (openBtn) {
                openBtn.onclick = () => {
                    this.trigger('open_clicked', { id: pinInfo.record.id });
                };
            }
        }
        /**
         * Get the fields' name and value to display in the popup.
         *
         * @private
         * @param {Object} pinInfo
         * @returns {Object} value contains the value of the field and string
         *                   contains the value of the xml's string attribute
         */
        _getPinPopupFields(pinInfo) {
            const record = pinInfo.record;
            const fieldsView = [];
            // INFO: Only display description in multi coordinates pin popup.
            if (pinInfo.ids.length > 1) {
                if (!this.props.hideDescription) {
                    fieldsView.push({
                        value: record.description,
                        string: this.env._t("Description"),
                    });
                }
                return fieldsView;
            }
            if (!this.props.hideName) {
                fieldsView.push({
                    value: record.display_name,
                    string: this.env._t("Name"),
                });
            }
            if (!this.props.hideDescription) {
                fieldsView.push({
                    value: record.description,
                    string: this.env._t("Description"),
                });
            }
            for (const field of this.props.locationFields) {
                if (record[field.fieldName]) {
                    const fieldName = record[field.fieldName] instanceof Array ?
                        record[field.fieldName][1] :
                        record[field.fieldName];
                    fieldsView.push({
                        value: fieldName,
                        string: field.string,
                    });
                }
            }
            return fieldsView;
        }
        /**
         * Remove the pins from the map and empty the pins array.
         *
         * @private
         */
        _removePins() {
            for (const pin of this.pins) {
                this.map.removeLayer(pin);
            }
            this.pins = [];
        }
        /**
         * Center the map on a certain pin and open the popup linked to it.
         *
         * @private
         * @param {Object} item
         */
        _centerAndOpenPin(item) {
            // this._createPinPopup({
            //     record: item,
            //     ids: [item.id],
            // });
            // this.map.panTo([
            //     item.latitude,
            //     item.longitude,
            // ], {
            //     animate: true,
            // });
        }
    }
    MapRenderer.props = {
        mapWidth: Number,
        mapHeight: Number,
        user_id: false,
        arch: Object,
        count: Number,
        offset: Number,
        limit: Number,
        records: Array,
        defaultOrder: {
            type: String,
            optional: true,
        },
        shouldUpdatePosition: Boolean,
        canRMBClick: Boolean,
        locationsFieldName: String,
        locationRelationFieldName: String,
        locationFieldsInfo: {
            type: Array,
            element: {
                type: Object,
                shape: {
                    target: String,
                    string: String,
                },
            },
        },
        levelFieldsInfo: {
            type: Array,
            element: {
                type: Object,
                shape: {
                    target: String,
                    string: String,
                },
            },
        },
        hasFormView: Boolean,
        isEmbedded: Boolean,
        noContentHelp: {
            type: String,
            optional: true,
        },
    };
    MapRenderer.template = 'syd_web_pin_map.MapRenderer';

    return MapRenderer;
});
