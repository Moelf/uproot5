# BSD 3-Clause License; see https://github.com/scikit-hep/uproot4/blob/main/LICENSE

"""
This module defines versionless models of ``TRef`` and ``TRefArray``.
"""


import struct
from collections.abc import Sequence

import numpy

import uproot

_tref_format1 = struct.Struct(">xxIxxxxxx")

# Note: https://github.com/root-project/root/blob/master/io/doc/TFile/TRef.txt
#       https://github.com/root-project/root/blob/master/io/doc/TFile/TRefArray.txt


class Model_TRef(uproot.model.Model):
    """
    A versionless :doc:`uproot.model.Model` for ``TRef``.

    This model does not deserialize all fields, only the reference number.
    """

    @property
    def ref(self):
        """
        The reference number as an integer.
        """
        return self._ref

    def read_numbytes_version(self, chunk, cursor, context):
        pass

    def read_members(self, chunk, cursor, context, file):
        if self.is_memberwise:
            raise NotImplementedError(
                """memberwise serialization of {}
in file {}""".format(
                    type(self).__name__, self.file.file_path
                )
            )
        self._ref = cursor.field(chunk, _tref_format1, context)

    def __repr__(self):
        return f"<TRef {self._ref}>"

    @classmethod
    def strided_interpretation(
        cls, file, header=False, tobject_header=True, breadcrumbs=(), original=None
    ):
        members = []
        members.append(("@pidf", numpy.dtype(">u2")))
        members.append(("ref", numpy.dtype(">u4")))
        members.append(("@other1", numpy.dtype(">u2")))
        members.append(("@other2", numpy.dtype(">u4")))

        return uproot.interpretation.objects.AsStridedObjects(
            cls, members, original=original
        )

    @classmethod
    def awkward_form(cls, file, context):
        awkward = uproot.extras.awkward()
        contents = {}
        if context["tobject_header"]:
            contents["@pidf"] = uproot._util.awkward_form(
                numpy.dtype("u2"), file, context
            )
            contents["ref"] = uproot._util.awkward_form(
                numpy.dtype("u4"), file, context
            )
            contents["@other1"] = uproot._util.awkward_form(
                numpy.dtype("u2"), file, context
            )
            contents["@other2"] = uproot._util.awkward_form(
                numpy.dtype("u4"), file, context
            )
        return awkward.forms.RecordForm(contents, parameters={"__record__": "TRef"})


_trefarray_format1 = struct.Struct(">i")
_trefarray_dtype = numpy.dtype(">i4")


class Model_TRefArray(uproot.model.Model, Sequence):
    """
    A versionless :doc:`uproot.model.Model` for ``TRefArray``.

    This also satisfies Python's abstract ``Sequence`` protocol.
    """

    @property
    def refs(self):
        """
        The reference number as a ``numpy.ndarray`` of ``dtype(">i4")``.
        """
        return self._data

    @property
    def nbytes(self):
        """
        The number of bytes in :ref:`uproot.models.TRef.Model_TRefArray.refs`.
        """
        return self._data.nbytes

    @property
    def name(self):
        """
        The name of this TRefArray.
        """
        return self._members["fName"]

    def read_members(self, chunk, cursor, context, file):
        forth = False
        forth_obj = None
        jump = True
        fcode_pre = []
        if "forth" in context.keys():
            awkward = uproot.extras.awkward()
            forth = True
            forth_obj = context["forth"]
            forth_obj.traverse_aform()
        if self.is_memberwise:
            raise NotImplementedError(
                """memberwise serialization of {}
in file {}""".format(
                    type(self).__name__, self.file.file_path
                )
            )
        cursor.skip(10)
        self._members["fName"] = cursor.string(chunk, context)
        self._members["fSize"] = cursor.field(chunk, _trefarray_format1, context)
        cursor.skip(6)
        self._data = cursor.array(
            chunk, self._members["fSize"], _trefarray_dtype, context
        )

    def __getitem__(self, where):
        return self._data[where]

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        if self.class_version is None:
            version = ""
        else:
            version = f" (version {self.class_version})"
        return "<{}{} {} at 0x{:012x}>".format(
            self.classname,
            version,
            numpy.array2string(
                self._data,
                max_line_width=numpy.inf,
                separator=", ",
                formatter={"float": lambda x: "%g" % x},
                threshold=6,
            ),
            id(self),
        )

    @classmethod
    def awkward_form(cls, file, context):
        awkward = uproot.extras.awkward()
        keys = context.keys()
        if "forth" in keys:
            forth_obj = context["forth"]
            forth_obj.forth_code[id(cls)] = None
            key = forth_obj.get_last_key()
            forth_obj.init_keys(cls, key + 1, key + 6)
            forth_obj.register_pre(cls)
            contents = {}
            contents["fName"] = awkward.forms.ListOffsetForm(
                context["index_format"],
                awkward.forms.NumpyForm(
                    (),
                    1,
                    "B",
                    parameters={"__array__": "char"},
                    form_key=f"node{key + 3}",
                ),
                parameters={
                    "__array__": "string",
                    "uproot": {
                        "as": "string",
                        "header": False,
                        "length_bytes": "1-5",
                    },
                },
                form_key=f"node{key + 2}",
            )
            context["prev-key"] = f"node{key + 4}"
            contents["fSize"] = uproot._util.awkward_form_forth(
                numpy.dtype("i4"), file, context
            )
            context["prev-key"] = f"node{key + 6}"
            contents["refs"] = awkward.forms.ListOffsetForm(
                context["index_format"],
                uproot._util.awkward_form_forth(numpy.dtype("i4"), file, context),
                form_key=f"node{key + 5}",
            )
            forth_obj.register_post(cls)
            del context["prev-key"]
            return awkward.forms.RecordForm(
                contents,
                parameters={"__record__": "TRefArray"},
                form_key=f"node{key + 1}",
            )
        else:
            contents = {}

            contents["fName"] = uproot.containers.AsString(
                False, typename="TString"
            ).awkward_form(file, context)
            contents["fSize"] = uproot._util.awkward_form(
                numpy.dtype("i4"), file, context
            )
            contents["refs"] = awkward.forms.ListOffsetForm(
                context["index_format"],
                uproot._util.awkward_form(numpy.dtype("i4"), file, context),
            )
            return awkward.forms.RecordForm(
                contents, parameters={"__record__": "TRefArray"}
            )


uproot.classes["TRef"] = Model_TRef
uproot.classes["TRefArray"] = Model_TRefArray
