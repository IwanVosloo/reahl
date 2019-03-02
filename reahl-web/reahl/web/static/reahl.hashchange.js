/* Copyright 2013-2018 Reahl Software Services (Pty) Ltd. All rights reserved. */
/*
    This file is part of Reahl.

    Reahl is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation; version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/


(function($) {
"use strict";

function getTraditionallyNamedFragment() {
    return mapToTraditionalNames($.deparam.fragment(window.location.hash));
}

function mapToTraditionalNames(untraditionallyNamedArguments) {
    var traditionallyNamedArguments = {};
    for (var cleanName in untraditionallyNamedArguments) {
        var value = untraditionallyNamedArguments[cleanName];
        var traditionalName;
        if (Array.isArray(value)) {
            traditionalName = cleanName+'[]';
        } else {
            traditionalName = cleanName;
        }
        traditionallyNamedArguments[traditionalName] = value;
    }
    return traditionallyNamedArguments;
}

function HashArgument(name, defaultValue) {
    this.name = name;
    this.value = defaultValue;
    this.changed = false;
    this.changeValue = function(value) {
        if (!_.isEqual(this.value, value)) {
            this.changed = true;
            this.value = value;
        }
    }

    this.getIsList = function() {
        return this.name.match('\\[\\]$');
    }

    this.getIsEmptyList = function() {
        return this.getIsList() && (_.isEqual(this.value, []));
    }

    this.getEmptyListSentinelName = function() {
        return this.name+'-';
    }

    this.getDefaultedSentinelName = function() {
        return this.name+'_';
    }
        
    this.updateFromHashObject = function(hashObject) {
        this.changed = false;
        var currentValue = hashObject[this.name];
        if (currentValue) {
            this.changeValue(currentValue);
        } else if (this.getIsList()) {
            if (hashObject[this.getEmptyListSentinelName()] != undefined) {
                this.changeValue([]);
            }
        } 
    }

    this.updateHashObject = function(hashObject) {
        delete hashObject[this.name];
        delete hashObject[this.getEmptyListSentinelName()];
        delete hashObject[this.getDefaultedSentinelName()];
        
        var nameInHash;
        var valueInHash;
        if (this.getIsEmptyList()) {
            nameInHash = this.getEmptyListSentinelName();
            valueInHash = '';
        } else {
            nameInHash = this.name;
            valueInHash = this.value;
        }

        hashObject[nameInHash] = valueInHash;
    }

    this.clearFromHashObject = function(hashObject) {
        this.deleteFromHashObject(hashObject);
        hashObject[this.getDefaultedSentinelName()] = '';
    }
        
    this.deleteFromHashObject = function(hashObject) {
        delete hashObject[this.name];
        delete hashObject[this.getEmptyListSentinelName()];
        delete hashObject[this.getDefaultedSentinelName()];
    }
}


$.widget('reahl.hashchange', {
    options: {
            url: '',
            cache: true,
            errorMessage: 'Ajax error',
            timeoutMessage: 'Ajax timeout',
            params: []
    },

    _create: function() {
        this.arguments = [];
        var _this = this;

        if (this.navigatedHereViaHistoryButtons()) {
            _this.reloadPage();
        }
        
        for (name in _this.options.params) {
            _this.arguments.push(new HashArgument(name, _this.options.params[name]))
        }

        var namespaced_submit = 'submit.'+this.element.attr('id');
        this.element.parents('form').off(namespaced_submit).on(namespaced_submit, function(e) {
            var form = $(this);
            _this.updateFormActionWithCurrentQueryString(form);
        });


        var namespaced_hashchange = 'hashchange.'+this.element.attr('id');
        $(window).off(namespaced_hashchange).on(namespaced_hashchange, function(e, isInitialPageLoad) {
            _this.handleHashChanged(function(){});
        });
        setTimeout(function() { $(window).trigger('hashchange', true); }, 0);
    },
    handleHashChanged: function(afterHandler) {
        var currentFragment = getTraditionallyNamedFragment();
        var changedArguments = this.calculateChangedArguments(currentFragment);
        if (this.hasChanged(changedArguments)) {
            this.triggerChange(currentFragment, changedArguments, afterHandler);
        };
    },
    navigatedHereViaHistoryButtons: function() {
        var performanceEntries = performance.getEntriesByType('navigation');
        if (performanceEntries.length == 1) {
            return (performanceEntries[0].type == 'back_forward');
        } else {
            return (performance.navigation.type == 2);
        }
    },
    reloadPage: function() {
        $('body').block({overlayCSS: {backgroundColor: '#fff', opacity: 0.3}, message: '', fadeIn: 0, fadeout: 0});
        location.reload(true);
    },
    getArgumentsAsObject: function() {
        var argumentObject = {};
        var argumentsArray = this.getArguments();
        for (var i=0; i<argumentsArray.length; i++) {
            var argument = argumentsArray[i];
            argumentObject[argument.name] = argument;
        };
        return argumentObject;
    },
    getArguments: function() {
        return this.arguments;
    },
    updateFormActionWithCurrentQueryString(form) {
        var fragmentInput = $('input[form="'+ form.attr('id')+'"][name="reahl-fragment"]');
        var completeFragment;
        var partialFragment;
        if (fragmentInput.length == 0) {
            fragmentInput = $('<input name="reahl-fragment" form="' + form.attr('id') + '" type="hidden">');
            fragmentInput.appendTo(form);
            partialFragment = getTraditionallyNamedFragment();
        } else {
            var handledFragmentPart = $.deparam.querystring(fragmentInput.val());
            partialFragment = $.extend(true, getTraditionallyNamedFragment(), handledFragmentPart);
        }
        
        completeFragment = this.addArgumentsToHash(partialFragment, this.getArguments());
        fragmentInput.val($.param(completeFragment, true));
    },
    addArgumentsToHash(currentHashValues, hashArguments) {
        var values = $.extend(true, {}, currentHashValues);
        for (var i=0; i<hashArguments.length; i++) {
            var argument = hashArguments[i];
            argument.updateHashObject(values);
        }
        return values;
    },
    calculatePOSTFragment(currentHashValues, hashArguments) {
        var values = this.addArgumentsToHash(currentHashValues, hashArguments);
        var relevantFormInputs = this.getFormInputsAsArguments(values);
        values = this.addArgumentsToHash(values, relevantFormInputs);
        var urlQueryString = $.deparam.querystring(this.options.url);
        for (var i in urlQueryString) {
            if (i in values){
                delete values[i];
            }
        };
        
        return values;
    },
    getFormInputsAsArguments: function(values){
        return $('.reahl-primitiveinput').map(function(i, v) { 
            var primitiveInput = $(v).data('reahlPrimitiveinput');
            return new HashArgument(primitiveInput.getName(), primitiveInput.getCurrentInputValue()); 
        }).filter(function(i,v){ return ! (v.name in values) });
    },
    triggerChange: function(currentHashValues, newArguments, afterHandler) {
        var _this = this;

        var data = {};
        data['reahl-fragment'] = $.param(_this.calculatePOSTFragment(currentHashValues, newArguments), true);  

        _this.element.block({overlayCSS: {backgroundColor: '#fff', opacity: 0.3}, message: '', fadeIn: 0, fadeout: 0});
        $.ajax({url:     this.options.url,
                method:  'POST',
                cache:   _this.options.cache,
                data:    data,
                success: function(data){
                    _this.element.html(data);
                    _this.arguments = newArguments;
                },
                complete: function(data){
                    _this.element.unblock();
                    afterHandler();
                },
                traditional: true
        });
    },
    hasChanged: function(newArguments){
        var _this = this;
        var changed = false;
        for (var i=0; i<newArguments.length; i++) {
            var argument = newArguments[i];
            if (argument.changed) {
                changed = true;
            };
        }
        return changed;
    },
    calculateChangedArguments: function(currentHashValues) {
        var _this = this;
        var hashArguments = $.extend(true, [], _this.getArguments());
        for (var i=0; i<hashArguments.length; i++) {
            var argument = hashArguments[i];
            argument.updateFromHashObject(currentHashValues);
        };
        return hashArguments;
    },
});

$.extend($.reahl.hashchange, {
    version: '1.8'
});


$.widget('reahl.changenotifier', {
    options: {
        name: undefined,
        widget_id: undefined,
        argument: undefined
    },
    _create: function() {
            var o = this.options;
            var element = this.element;
            var _this = this;
        
            if (!o.name) { throw new Error("No name given in options. This is a required option.")}

            $(element).attr('data-target-widget', o.widget_id);
            $(element).on( 'change', function(e) {
                if (_this.getIsSelfValid()) {
                    _this.updateCurrentValue(e.target);
                }
                if (_this.getIsValid()) {
                    var currentFragment = getTraditionallyNamedFragment();
                    _this.updateHashWithAllSiblingValues(currentFragment);
                    this.focus();
                    _this.unblockWidget();
                } else { _this.blockWidget(); }
                return true;
            });
    },
    getCurrentInputValue: function(currentInput) {
        var primitiveInput = $(currentInput).data('reahlPrimitiveinput');
        return primitiveInput.getCurrentInputValue();
    },
    getArgument: function(currentInput) {
        if (this.options.argument == undefined) {
            this.options.argument = new HashArgument(this.options.name, this.getCurrentInputValue(currentInput));
        }
        return this.options.argument;
    },
    updateCurrentValue: function(currentInput) {
        this.getArgument(currentInput).changeValue(this.getCurrentInputValue(currentInput));
    },
    updateHashWithAllSiblingValues: function(currentFragment) {
        this.getSiblingChangeNotifiers().each(function() {
            this.addCurrentInputValueTo(currentFragment);
            
        });
        var newHash = $.param(currentFragment, true);

        var form = this.getForm();
        form.block({overlayCSS: {backgroundColor: '#fff', opacity: 0.3}, message: '', fadeIn: 0, fadeout: 0});

//        history.replaceState(null, null, '#'+newHash);
        history.replaceState(null, null, '#'+newHash);

        this.getCorrespondingHashChangeHandler().handleHashChanged(function(){ form.unblock(); });
    },
    addCurrentInputValueTo: function(fragment) {
        var argument = this.options.argument;
        if (argument !== undefined) {
            argument.updateHashObject(fragment);
        }
    },
    getInputs: function() {
        if (this.element[0].form !== undefined) {
            return this.element;
        } else {
            return this.element.find('input');
        }
    },
    getForm: function() {
        return $(this.getInputs()[0].form);
    },
    getIsSelfValid: function() {
        var validator = this.getForm().data('validator');
        return validator.element(this.getInputs());
    },
    getCorrespondingHashChangeHandler: function() {
        return $('#'+this.options.widget_id).data('reahlHashchange');
    },
    getSiblings: function() {
        return $('[data-target-widget="' + this.options.widget_id + '"]');
    },
    getSiblingChangeNotifiers: function() {
        return this.getSiblings().map(function() {
            return $(this).data('reahlChangenotifier')
        });
    },
    getIsSiblingArgumentsValid: function() {
        var _this = this;
        var valid = true;
        this.getSiblingChangeNotifiers().each(function() {
            var sibling = this;
            if (sibling !== _this) {
                valid = valid && sibling.getIsSelfValid();
            }
        });
        return valid;
    },
    getIsValid: function() {
        return this.getIsSelfValid() && this.getIsSiblingArgumentsValid();
    },
    blockWidget: function() {
        $('#'+this.options.widget_id).block({overlayCSS: {backgroundColor: '#fff', opacity: 0.3}, message: '', fadeIn: 0, fadeout: 0});
    },
    unblockWidget: function() {
        $('#'+this.options.widget_id).unblock();
    }
});

$.extend($.reahl.changenotifier, {
version: '1.0'
});


})(jQuery);


