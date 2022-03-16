from OpenGL.GL import *
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5 import QtCore
import numpy as np
import copy
from mwcapture.libmwcapture import *

g_str_v_yuyv="""
    #version 130
    in vec2 vertexIn;
    in vec2 textureIn;
    out vec2 textureOut;
    void main(void){
        gl_Position = vec4(vertexIn,0.0,1);
        textureOut = textureIn;
    }
    """

g_str_f_yuyv="""
    #version 130
    uniform sampler2D tex_yuv;
    uniform int cx;
    uniform int cy;
    in vec2 textureOut;
    void main(void){
        vec3 rgb;
        vec3 yuv;
        highp float fxDD;
        int t_cx = cx;
        int t_cy = cy;
        highp float width = float(t_cx);
        float r,g,b,y,u,v;
        int x = int(floor(width*textureOut.x));
        int imod = int(x/2);
        int t_imod = imod;
        int i = x-(t_imod*2);
        if(i==0){
            fxDD = textureOut.x + (1.0f/width);
            y = texture2D(tex_yuv,textureOut).r;
            u = texture2D(tex_yuv,textureOut).g;
            v = texture2D(tex_yuv,vec2(fxDD,textureOut.y)).g;
        }else{
            fxDD = textureOut.x - (1.0f/width);
            y = texture2D(tex_yuv,textureOut).r;
            u = texture2D(tex_yuv,vec2(fxDD,textureOut.y)).g;
            v = texture2D(tex_yuv,textureOut).g;
        }
        y = 1.1643*(y-0.0625);
        u = u - 0.5;
        v = v - 0.5;
        r = y + 1.5958*v;
        g = y - 0.39173*u - 0.81290*v;
        b = y + 2.017*u;
        gl_FragColor=vec4(r,g,b,1.0);
    }
    """

g_str_v_nv12 ="""
    #version 130
	in vec2 vertexIn;
	in vec2 textureIn;
	in vec2 textureIn2;
	out vec2 textureOut;
	out vec2 textureOut2;
	void main(void)
	{
	  gl_Position = vec4(vertexIn, 0.0, 1);
	  textureOut = textureIn;
	  textureOut2 = textureIn2;
	}
"""

g_str_f_nv12 = """
	#version  130
	in vec2 textureOut;
	in vec2 textureOut2;
	uniform sampler2D tex_nv12;
	uniform int cx;
	uniform int cy;
	void main(void)
	{
	  float r, g, b, my, mu, mv;
	  highp float fxDD,fyDD;
	  int t_cx = cx;
	  int t_cy = cy;
	  highp float width = float(t_cx);
	  highp float height = float(t_cy);
	  my = texture2D(tex_nv12, vec2(textureOut.x,textureOut.y)).r;
	  int x = int(floor(width*textureOut2.x));
	  int imod = int(x/2);
	  int t_imod = imod;
	  int i = x - (t_imod*2);
	  if(i==0)
	  {
	    fxDD = textureOut2.x + (1.0f/width);
	    mu = texture2D(tex_nv12, vec2(textureOut2.x,textureOut2.y)).r;
	    mv = texture2D(tex_nv12, vec2(fxDD,textureOut2.y)).r;
	  }
	  else
	  {
	    fxDD = textureOut2.x - (1.0f/width);
	    mu = texture2D(tex_nv12, vec2(fxDD,textureOut2.y)).r;
	    mv = texture2D(tex_nv12, vec2(textureOut2.x,textureOut2.y)).r;
	  }
	  my = 1.1643*(my-0.0625);
	  mu = mu - 0.5;
	  mv = mv - 0.5;
	  r = my+1.5958*mv;
	  g = my-0.39173*mu-0.81290*mv;
	  b = my+2.017*mu;
	  gl_FragColor=vec4(r,g,b,1.0);
	}
"""

g_ver_vertices = np.array([-1.0,-1.0,1.0,-1.0,-1.0,1.0,1.0,1.0],dtype=np.float32)
g_ver_textures = np.array([0.0,1.0,1.0,1.0,0.0,0.0,1.0,0.0],dtype=np.float32)
g_ver_textures2 = np.array([0.0,0.5,1.0,0.5,0.0,0.0,1.0,0.0],dtype=np.float32)
g_ver_textures3 = np.array([0.0,0.75,1.0,0.75,0.0,0.5,1.0,0.5],dtype=np.float32)
#g_ver_textures = np.array([1.0,1.0,0.0,1.0,0.0,0.0,1.0,0.0],dtype=np.float32)


class CRenderWid(QOpenGLWidget):
    def __init__(self, parent=None, flags = QtCore.Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)
        self.m_f_r = 1.0
        self.m_f_g = 1.0
        self.m_f_b = 1.0
        self.m_glsl_text = 0
        self.m_glsl_shader_v = 0
        self.m_glint_len_shader_v = GLint(0)
        self.m_glsl_shader_f = 0
        self.m_glint_len_shader_f = GLint(0)
        self.m_glsl_program_yuyv = 0
        self.m_glsl_fbo = 0
        self.m_glsl_rbo = 0
        self.m_data = 0
        self.m_fourcc = 0
        self.m_cx = 0
        self.m_cy = 0
        self.m_b_black = True

    def __del__(self):
        pass

    def initializeGL(self):
        print(glGetString(GL_VERSION))

    def paintGL(self):
        if self.m_data!= 0:
            if self.m_fourcc == MWFOURCC_YUY2:
                self.render_yuy2(1)
            elif self.m_fourcc == MWFOURCC_YUYV:
                self.render_yuy2(1)
            elif self.m_fourcc == MWFOURCC_NV12:
                self.render_nv12(1)
            else:
                glClear(GL_COLOR_BUFFER_BIT)
                glClearColor(0.0,0.0,0.0,1.0)    
        else:
            glClear(GL_COLOR_BUFFER_BIT)
            glClearColor(0.0,0.0,0.0,1.0)

    def resizeGL(self, x, y):
        self.makeCurrent()
        glViewport(0,0,x,y)

    def open_render(self,fourcc,cx,cy):
        self.abolish_render()
        t_b_ret = False
        if fourcc == MWFOURCC_YUY2:
            t_b_ret = self.setup_render_for_yuy2(cx,cy)
        elif fourcc == MWFOURCC_YUY2:
            t_b_ret = self.setup_render_for_yuy2(cx,cy)
        elif fourcc == MWFOURCC_NV12:
            t_b_ret = self.setup_render_for_nv12(cx,cy)
        if t_b_ret == True:
            self.m_fourcc = fourcc
            self.m_cx = cx
            self.m_cy = cy
        else:
            self.m_fourcc = 0
            self.m_cx = 0
            self.m_cy = 0
        return t_b_ret 

    def setup_render_for_yuy2(self,cx,cy):
        self.makeCurrent()
        self.m_glsl_text = glGenTextures(1)
        if self.m_glsl_text == 0:
            self.abolish_render()
            return False
        glBindTexture(GL_TEXTURE_2D,self.m_glsl_text)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE)

        self.m_glsl_shader_v = glCreateShader(GL_VERTEX_SHADER)
        if self.m_glsl_shader_v == 0:
            self.abolish_render()
            return False
        self.m_glsl_shader_f = glCreateShader(GL_FRAGMENT_SHADER)
        if self.m_glsl_shader_f == 0:
            self.abolish_render()
            return False
        glShaderSource(self.m_glsl_shader_v,g_str_v_yuyv)
        glShaderSource(self.m_glsl_shader_f,g_str_f_yuyv)

        glCompileShader(self.m_glsl_shader_v)
        t_status = glGetShaderiv(self.m_glsl_shader_v,GL_COMPILE_STATUS)
        if not(t_status):
            print("v----------\n\n%s\n\n________\n" % (glGetShaderInfoLog(self.m_glsl_shader_v)))
            self.abolish_render()
            return False
        
        glCompileShader(self.m_glsl_shader_f)
        t_status = glGetShaderiv(self.m_glsl_shader_f,GL_COMPILE_STATUS)
        if not(t_status):
            print("f----------\n\n%s\n\n________\n" % (glGetShaderInfoLog(self.m_glsl_shader_f)))
            self.abolish_render()
            return False

        self.m_glsl_program_yuyv = glCreateProgram()
        glAttachShader(self.m_glsl_program_yuyv,self.m_glsl_shader_v)
        glAttachShader(self.m_glsl_program_yuyv,self.m_glsl_shader_f)
        glLinkProgram(self.m_glsl_program_yuyv)
        t_status = glGetProgramiv(self.m_glsl_program_yuyv,GL_LINK_STATUS)
        if not(t_status):
            self.abolish_render()
            return False
        
        self.m_glsl_yuyv_ver_loc = glGetAttribLocation(self.m_glsl_program_yuyv,"vertexIn");
        self.m_glsl_yuyv_tex_loc = glGetAttribLocation(self.m_glsl_program_yuyv,"textureIn");
        self.m_glsl_yuyv_tex2_loc = glGetAttribLocation(self.m_glsl_program_yuyv,"textureIn2");

        glVertexAttribPointer(self.m_glsl_yuyv_ver_loc,2,GL_FLOAT,0,0,g_ver_vertices)
        glEnableVertexAttribArray(self.m_glsl_yuyv_ver_loc)
        glVertexAttribPointer(self.m_glsl_yuyv_tex_loc,2,GL_FLOAT,0,0,g_ver_textures)
        glEnableVertexAttribArray(self.m_glsl_yuyv_tex_loc)
        glVertexAttribPointer(self.m_glsl_yuyv_tex2_loc,2,GL_FLOAT,0,0,)

        self.m_glsl_fbo = glGenFramebuffers(1)
        if not(self.m_glsl_fbo):
            self.abolish_render()
            return False

        glBindFramebuffer(GL_FRAMEBUFFER,self.m_glsl_fbo)
        self.m_glsl_rbo = glGenRenderbuffers(1)
        if not(self.m_glsl_rbo):
            self.abolish_render()
            return False

        glBindRenderbuffer(GL_RENDERBUFFER,self.m_glsl_rbo)
        glRenderbufferStorage(GL_RENDERBUFFER,GL_RGBA8,cx,cy)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_RENDERBUFFER,self.m_glsl_rbo)
        glBindFramebuffer(GL_FRAMEBUFFER,0)

        return True

    def setup_render_for_nv12(self,cx,cy):
        self.makeCurrent()
        self.m_glsl_text = glGenTextures(1)
        if self.m_glsl_text == 0:
            self.abolish_render()
            return False
        glBindTexture(GL_TEXTURE_2D,self.m_glsl_text)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE)

        self.m_glsl_shader_v = glCreateShader(GL_VERTEX_SHADER)
        if self.m_glsl_shader_v == 0:
            self.abolish_render()
            return False
        self.m_glsl_shader_f = glCreateShader(GL_FRAGMENT_SHADER)
        if self.m_glsl_shader_f == 0:
            self.abolish_render()
            return False
        glShaderSource(self.m_glsl_shader_v,g_str_v_nv12)
        glShaderSource(self.m_glsl_shader_f,g_str_f_nv12)

        glCompileShader(self.m_glsl_shader_v)
        t_status = glGetShaderiv(self.m_glsl_shader_v,GL_COMPILE_STATUS)
        if not(t_status):
            print("v----------\n\n%s\n\n________\n" % (glGetShaderInfoLog(self.m_glsl_shader_v)))
            self.abolish_render()
            return False
        
        glCompileShader(self.m_glsl_shader_f)
        t_status = glGetShaderiv(self.m_glsl_shader_f,GL_COMPILE_STATUS)
        if not(t_status):
            print("f----------\n\n%s\n\n________\n" % (glGetShaderInfoLog(self.m_glsl_shader_f)))
            self.abolish_render()
            return False

        self.m_glsl_program_yuyv = glCreateProgram()
        glAttachShader(self.m_glsl_program_yuyv,self.m_glsl_shader_v)
        glAttachShader(self.m_glsl_program_yuyv,self.m_glsl_shader_f)
        glLinkProgram(self.m_glsl_program_yuyv)
        t_status = glGetProgramiv(self.m_glsl_program_yuyv,GL_LINK_STATUS)
        if not(t_status):
            self.abolish_render()
            return False
        
        self.m_glsl_yuyv_ver_loc = glGetAttribLocation(self.m_glsl_program_yuyv,"vertexIn");
        self.m_glsl_yuyv_tex_loc = glGetAttribLocation(self.m_glsl_program_yuyv,"textureIn");
        self.m_glsl_yuyv_tex2_loc = glGetAttribLocation(self.m_glsl_program_yuyv,"textureIn2");

        glVertexAttribPointer(self.m_glsl_yuyv_ver_loc,2,GL_FLOAT,0,0,g_ver_vertices)
        glEnableVertexAttribArray(self.m_glsl_yuyv_ver_loc)
        glVertexAttribPointer(self.m_glsl_yuyv_tex_loc,2,GL_FLOAT,0,0,g_ver_textures2)
        glEnableVertexAttribArray(self.m_glsl_yuyv_tex_loc)
        glVertexAttribPointer(self.m_glsl_yuyv_tex2_loc,2,GL_FLOAT,0,0,g_ver_textures3)
        glEnableVertexAttribArray(self.m_glsl_yuyv_tex2_loc)

        self.m_glsl_fbo = glGenFramebuffers(1)
        if not(self.m_glsl_fbo):
            self.abolish_render()
            return False

        glBindFramebuffer(GL_FRAMEBUFFER,self.m_glsl_fbo)
        self.m_glsl_rbo = glGenRenderbuffers(1)
        if not(self.m_glsl_rbo):
            self.abolish_render()
            return False

        glBindRenderbuffer(GL_RENDERBUFFER,self.m_glsl_rbo)
        glRenderbufferStorage(GL_RENDERBUFFER,GL_RGBA8,cx,cy)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_RENDERBUFFER,self.m_glsl_rbo)
        glBindFramebuffer(GL_FRAMEBUFFER,0)

        return True

    def abolish_render(self):
        self.makeCurrent()
        if self.m_glsl_fbo !=0:
            glDeleteFramebuffers(1,[self.m_glsl_fbo])
            self.m_glsl_fbo = 0

        if self.m_glsl_rbo != 0:
            glDeleteRenderbuffers(1,[self.m_glsl_rbo])
            self.m_glsl_rbo = 0

        if self.m_glsl_shader_v != 0:
            glDeleteShader(self.m_glsl_shader_v)
            self.m_glsl_shader_v = 0

        if self.m_glsl_shader_f != 0:
            glDeleteShader(self.m_glsl_shader_f)
            self.m_glsl_shader_f = 0

        if self.m_glsl_program_yuyv != 0:
            glDeleteProgram(self.m_glsl_program_yuyv)
            self.m_glsl_program_yuyv = 0

        if self.m_glsl_text != 0:
            glDeleteTextures(1,[self.m_glsl_text])

    def render_yuy2(self,pbframe):
        self.makeCurrent()
        if pbframe == 0:
            glClear(GL_COLOR_BUFFER_BIT)
            glClearColor(0.0,0.0,0.0,1.0)
            return True
        glBindFramebuffer(GL_FRAMEBUFFER,self.m_glsl_fbo)
        glUseProgram(self.m_glsl_program_yuyv)
        glViewport(0,0,self.m_cx,self.m_cy)
        #glViewport(0,0,self.width(),self.height())

        glClear(GL_COLOR_BUFFER_BIT)
        glClearColor(0.0,0.0,0.0,1.0)
        
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D,self.m_glsl_text)

        if pbframe!=0:
            glTexImage2D(GL_TEXTURE_2D,0,GL_RG,self.m_cx,self.m_cy,0,GL_RG,GL_UNSIGNED_BYTE,self.m_data)
        
        glUniform1i(glGetUniformLocation(self.m_glsl_program_yuyv,"tex_yuv"),0)
        glUniform1i(glGetUniformLocation(self.m_glsl_program_yuyv,"cx"),self.m_cx)
        glUniform1i(glGetUniformLocation(self.m_glsl_program_yuyv,"cy"),self.m_cy)

        glDrawArrays(GL_TRIANGLE_STRIP,0,4)
        glBindFramebuffer(GL_FRAMEBUFFER,0)

        glBindFramebuffer(GL_READ_FRAMEBUFFER,self.m_glsl_fbo)
        glViewport(0,0,self.width(),self.width())
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER,self.defaultFramebufferObject())
        glBlitFramebuffer(0,0,self.m_cx,self.m_cy,0,0,self.width(),self.height(),GL_COLOR_BUFFER_BIT,GL_NEAREST)

        return True

    def render_nv12(self,pbframe):
        self.makeCurrent()
        if pbframe == 0:
            glClear(GL_COLOR_BUFFER_BIT)
            glClearColor(0.0,0.0,0.0,1.0)
            return True
        glBindFramebuffer(GL_FRAMEBUFFER,self.m_glsl_fbo)
        glUseProgram(self.m_glsl_program_yuyv)
        glViewport(0,0,self.m_cx,self.m_cy)
        #glViewport(0,0,self.width(),self.height())

        glClear(GL_COLOR_BUFFER_BIT)
        glClearColor(0.0,0.0,0.0,1.0)
        
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D,self.m_glsl_text)

        if pbframe!=0:
            glTexImage2D(GL_TEXTURE_2D,0,GL_RED,self.m_cx,self.m_cy*2,0,GL_RED,GL_UNSIGNED_BYTE,self.m_data)
        
        glUniform1i(glGetUniformLocation(self.m_glsl_program_yuyv,"tex_nv12"),0)
        glUniform1i(glGetUniformLocation(self.m_glsl_program_yuyv,"cx"),self.m_cx)
        glUniform1i(glGetUniformLocation(self.m_glsl_program_yuyv,"cy"),self.m_cy)

        glDrawArrays(GL_TRIANGLE_STRIP,0,4)
        glBindFramebuffer(GL_FRAMEBUFFER,0)

        glBindFramebuffer(GL_READ_FRAMEBUFFER,self.m_glsl_fbo)
        glViewport(0,0,self.width(),self.width())
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER,self.defaultFramebufferObject())
        glBlitFramebuffer(0,0,self.m_cx,self.m_cy,0,0,self.width(),self.height(),GL_COLOR_BUFFER_BIT,GL_NEAREST)

        return True

    def put_frame(self, pbframe):
        self.m_data = copy.deepcopy(pbframe)
        self.update()
        
    def set_black(self):
        self.m_data = 0
        self.update()
