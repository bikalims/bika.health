from bika.health import bikaMessageFactory as _
from bika.lims.utils import t
from bika.lims.browser.analysisrequest.add import ajaxAnalysisRequestSubmit as BaseClass
from bika.lims.utils import tmpID
from bika.lims.idserver import renameAfterCreation
from bika.lims.browser.analysisrequest.add import ajax_form_error
from Products.CMFCore.utils import getToolByName
import json


class AnalysisRequestSubmit(BaseClass):

    def __call__(self):

        # Create new Anonymous Patients as needed
        uc = getToolByName(self.context, 'uid_catalog')
        bpc = getToolByName(self.context, 'bika_patient_catalog')
        form = self.request.form
        formc = self.request.form.copy()
        state = json.loads(formc['state'])
        for key in state.keys():
            values = state[key].copy()
            patuid = values.get('Patient', '')
            if patuid == '' and values.get('Analyses') != []:
                msg = t(_('Required fields have no values: Patient'))
                ajax_form_error(self.errors, arnum=key, message=msg)
                continue
            elif patuid == 'anonymous':
                clientpatientid = values.get('ClientPatientID', '')
                # Check if has already been created
                proxies = bpc(getClientPatientID=clientpatientid)
                if proxies and len(proxies) > 0:
                    patient = proxies[0].getObject()
                else:
                    # Create an anonymous patient
                    client = uc(UID=values['Client'])[0].getObject()
                    _id = client.patients.invokeFactory('Patient', id=tmpID())
                    patient = client.patients[_id]
                    patient.edit(Anonymous = 1,
                                 Gender = "dk",
                                 PrimaryReferrer = client.UID(),
                                 Firstname = _("AP"),
                                 Surname = clientpatientid,
                                 ClientPatientID = clientpatientid)
                    patient.unmarkCreationFlag()
                    patient.reindexObject()
                    client.reindexObject()
                    renameAfterCreation(patient)

                values['Patient']=patient.UID()
                state[key] = values
        formc['state'] = json.JSONEncoder().encode(state)
        self.request.form = formc
        return BaseClass.__call__(self)
