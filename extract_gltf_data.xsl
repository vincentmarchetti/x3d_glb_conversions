<?xml version="1.0" encoding="utf-8"?>
<!--
(MIT License)

Copyright 2017 Vincent Marchetti  vmarchetti@kshell.com

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
-->

<xsl:stylesheet version="1.0" 
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:gltf="http://www.kshell.com/ns/gltf">

<xsl:output method="xml" encoding="utf-8"/>

<xsl:template match="/">
<input_nodes>
<xsl:apply-templates select="//gltf:*"/>
</input_nodes>
</xsl:template>

<!-- this template copies everything, but flattens all elements into no-namespace -->
<xsl:template match="*">
    <xsl:element name="{local-name()}" namespace="">
        <xsl:apply-templates select="*|@*|node()"/>
    </xsl:element>
</xsl:template>

<xsl:template match="@*|text()">
    <xsl:copy>
        <xsl:apply-templates select="*|@*|node()"/>
    </xsl:copy>
</xsl:template>

</xsl:stylesheet>
