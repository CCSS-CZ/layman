/*
    LayMan - the Layer Manager

    Copyright (C) 2016 Czech Centre for Science and Society
    Authors: Jachym Cepicky, Karel Charvat, Stepan Kafka, Michal Sredl, Premysl Vohnout
    Mailto: sredl@ccss.cz, charvat@ccss.cz

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

// Model for getCkanResources()
Ext4.define('HSRS.LayerManager.CkanPanel.ResourceModel', {
        extend: 'Ext4.data.Model',
        fields: [
            {name: 'name', mapping: 'name', type: Ext4.data.Types.STRING},
            {name: 'url', mapping: 'url', type: Ext4.data.Types.STRING},
            {name: 'format', mapping: 'format', type: Ext4.data.Types.STRING},
            {name: 'description', mapping: 'description', type: Ext4.data.Types.STRING}
        ]

});

// Model for getCkanPackages() (datasets)
Ext4.define('HSRS.LayerManager.CkanPanel.PackageModel', {
        extend: 'Ext4.data.Model',
        fields: [
            {name: 'organizationName', mapping: 'organizationName', type: Ext4.data.Types.STRING},
            {name: 'organizationTitle', mapping: 'organizationTitle', type: Ext4.data.Types.STRING},
            {name: 'name',  mapping: 'name', type: Ext4.data.Types.STRING},
            {name: 'title',  mapping: 'title', type: Ext4.data.Types.STRING},
            {name: 'notes',  mapping: 'notes', type: Ext4.data.Types.STRING}
        ]

});

